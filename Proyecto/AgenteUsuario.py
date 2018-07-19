from imports import *

__author__ = 'alejandro'

argumentos = getArguments(my_port=8000)
#Direcciones hardcodeadas (propia)
host = argumentos['host']
port = argumentos['port']

#Nombre del usuario (solo )
name = argumentos['name']

directorio_host = argumentos['dir_host']
directorio_port = argumentos['dir_port']

addr = argumentos['addr']


agn = getAgentNamespace()

ont = Namespace('Ontologias/root-ontology.owl')

#Objetos agente
AgenteUsuario = Agent('AgenteUsuario',agenteUsuario_ns[name],formatDir(addr,port) + '/comm',None)
DirectorioAgentes = Agent('DirectorioAgentes',agn.Directory,formatDir(directorio_host,directorio_port) + '/comm',None)


productos_a_opinar_db = 'AgenteUsuario/Opinar/%s.turtle'
recomendaciones_db = 'AgenteUsuario/Recomendaciones/%s.turtle'
productos_db = 'Datos/productos.turtle'
carrito_db = 'AgenteUsuario/Carritos/%s.turtle'
pedidos_db = 'AgenteUsuario/Pedidos/%s.turtle'
envios_db = 'AgenteUsuario/Envios/%s.turtle'

#En los pedidos se guardan los productos comprados que ya han sido enviados (y que por tanto pueden 
# ser devueltos)
productos_a_opinar = Graph()
recomendaciones = Graph()
carrito = Graph()
pedidos = Graph()
envios = Graph()

carritoFalso = Graph()



#Acciones. Este diccionario sera cargado con todos los procedimientos que hay que llamar dinamicamente 
# cuando llega un mensaje
actions = {}


app = Flask(__name__,template_folder="AgenteUsuario/templates")

def getDatos():
    datos = [
        {
            'db':productos_a_opinar_db,
            'graph':productos_a_opinar
        },
        {
            'db':recomendaciones_db,
            'graph':recomendaciones
        },
        {
            'db':carrito_db,
            'graph':carrito
        },
        {
            'db':pedidos_db,
            'graph':pedidos
        },
        {
            'db':envios_db,
            'graph':envios
        }
    ]
    return datos
def cargarCarritoFalso():
    global carritoFalso
    if os.path.isfile('AgenteUsuario/carritoFalso.turtle'):
        carritoFalso.parse('AgenteUsuario/carritoFalso.turtle',format='turtle')

#Carga el grafo rdf del fichero graphFile
def cargarGrafos():

    datos = getDatos()
    for s in datos:
        file = s['db']%name
        if os.path.isfile(file):
            s['graph'].parse(file,format="turtle")

def guardarGrafo(g):
    datos = getDatos()
    for d in datos:
        if d['graph'] is g:
            g.serialize(d['db']%name,format="turtle")

@app.route("/")
def main_page():
    """
    El hola mundo de los servicios web
    :return:
    """
    return render_template('main.html')

def calcularTotalCarrito():
    total = 0
    for p in carrito.subjects(RDF.type,productos_ns.type):
        try:
            total += int(carrito.value(p,productos_ns.Importe)) * int(carrito.value(p,productos_ns.Cantidad))
        except ValueError:
            pass

    return total

@app.route("/carrito")
def verCarrito():
    total = calcularTotalCarrito()
    list = []
    for p in carrito.subjects(RDF.type,productos_ns.type):
        dict = {}
        dict['Nombre'] = carrito.value(p,productos_ns.Nombre)
        dict['Cantidad'] = carrito.value(p,productos_ns.Cantidad)
        dict['Subtotal'] = carrito.value(p,productos_ns.Importe)
        try:
            dict['Total'] = str(int(dict['Subtotal']) * int(dict['Cantidad']))
        except ValueError:
            dict['Total'] = 0
        list+=[dict]

    return render_template('carrito.html',list=list,total=total,name=name)

def vaciarCarritoFun():
    global carrito
    carrito = Graph()
    guardarGrafo(carrito)

@app.route("/vaciarCarrito")
def vaciarCarrito():
    vaciarCarritoFun()
    return redirect("/carrito")

def enviarPedidoATienda(pedido):

    obj = createAction(AgenteUsuario,'nuevoPedido')
    pedido.add((obj, RDF.type, agn.UsuarioNuevoPedido))
    msg = build_message(pedido,
        perf=ACL.request,
        sender=AgenteUsuario.uri,
        content=obj)

    # Enviamos el mensaje a cualquier agente admisor
    send_message_any(msg,AgenteUsuario,DirectorioAgentes,agenteReceptor_ns.type)


@app.route("/checkout")
def checkout():
    global pedidos
    prioridad = request.args['prioridad']
    direccion = request.args['direccion']
    cp = request.args['cp']

    pedido = Graph()
    pedido_id = str(random.getrandbits(64))
    pedido.add((pedidos_ns[pedido_id],RDF.type,pedidos_ns.type))
    pedido.add((pedidos_ns[pedido_id],pedidos_ns.Id,Literal(pedido_id)))
    pedido.add((pedidos_ns[pedido_id],pedidos_ns.Hechopor,agenteUsuario_ns[name]))
    pedido.add((pedidos_ns[pedido_id],pedidos_ns.Prioridad,Literal(prioridad)))
    pedido.add((pedidos_ns[pedido_id],pedidos_ns.Importetotal,Literal(calcularTotalCarrito())))
    pedido.add((pedidos_ns[pedido_id], pedidos_ns.Fecharealizacion,Literal(getCurrentDate())))

    node =  pedidos_ns[pedido_id + '-listaProductos']

    pedido.add((pedidos_ns[pedido_id],pedidos_ns.Contiene,node))

    c = Collection(pedido,node)

    for p in carrito.subjects(predicate=RDF.type,object=productos_ns.type):
        for i in range(int(carrito.value(p,productos_ns.Cantidad))):
            idProd = carrito.value(p,productos_ns.Id)
            prodGraph = Graph()
            idProductoPedido = str(random.getrandbits(64))
            productoPedido = productosPedido_ns[idProductoPedido]

            prodGraph.add((productoPedido,RDF.type,productosPedido_ns.type))
            prodGraph.add((productoPedido,productosPedido_ns.Id,Literal(idProductoPedido)))
            prodGraph.add((productoPedido,productosPedido_ns.AsociadoAlProducto,productos_ns[idProd]))

            pedido += prodGraph
            c.append(productoPedido)
    


    add_localizacion_node(pedido,pedidos_ns[pedido_id],pedidos_ns.Tienedirecciondeentrega,direccion,cp)

    #Enviar mensaje a la tienda
    enviarPedidoATienda(pedido)
    vaciarCarritoFun()
    pedidos += pedido
    guardarGrafo(pedidos)

    return redirect("/")

@app.route("/anadirProductoCarrito")
def anadirProductoCarrito():
    dict = request.args
    ref = dict['ref']
    id = dict['id']
    importe = dict['importe']
    nombre = dict['nombre']

    try:
        carrito.triples((productos_ns[id],None,None)).next()
        value = carrito.value(productos_ns[id],productos_ns.Cantidad)
        carrito.set((productos_ns[id],productos_ns.Cantidad,Literal(int(value)+1)))
        guardarGrafo(carrito)
    except StopIteration:
        carrito.add((productos_ns[id], productos_ns.Id,Literal(id)))
        carrito.add((productos_ns[id], productos_ns.Importe,Literal(importe)))
        carrito.add((productos_ns[id], productos_ns.Nombre,Literal(nombre)))
        carrito.add((productos_ns[id], productos_ns.Cantidad,Literal(1)))
        carrito.add((productos_ns[id], RDF.type, productos_ns.type))
        guardarGrafo(carrito)
    except ValueError:
        return "Error en el formato de los numeros"

    return redirect("/" + ref)
@app.route("/recomendaciones")
def verRecomendaciones():
    l = []
    g = recomendaciones
    #Todos los productos tienen el predicado "type" a productos.type.
    #De esta forma los obtenemos con mas facilidad y sin consulta sparql
    #La funcoin subjects retorna los sujetos con tal predicado y objeto
    for s in g.subjects(predicate=RDF.type,object=productos_ns.type):
        # Anadimos los atributos que queremos renderizar a la vista
        dic = {}
        dic['nombre'] = g.value(subject = s,predicate = productos_ns.Nombre)
        dic['importe'] = g.value(subject = s,predicate = productos_ns.Importe)
        dic['id'] = g.value(subject = s,predicate = productos_ns.Id)
        l = l + [dic]

    #Renderizamos la vista
    return render_template('recomendaciones.html',list=l)

@app.route("/pedidos")
def verPedidos():
    l = []
    g = pedidos
    for s in g.subjects(predicate=RDF.type,object=pedidos_ns.type):
        # Anadimos los atributos que queremos renderizar a la vista
        dic = {}
        dic['ID'] = g.value(subject = s,predicate = pedidos_ns.Id)
        dic['Direccion Entrega'] = g.value(subject = s,predicate = pedidos_ns.Tienedirecciondeentrega)
        dic['Fecha Realizacion'] = g.value(subject = s, predicate = pedidos_ns.Fecharealizacion)

        prods = []
        container = g.value(subject=s,predicate=pedidos_ns.Contiene)
        c = Collection(g,container)
        for item in c:
            dict = {}
            n = g.value(subject=item,predicate=productosPedido_ns.AsociadoAlProducto)
            dict['ID'] = n
            prods += [dict]
        dic['Productos'] = prods
        l = l + [dic]

    #Renderizamos la vista
    return render_template('pedidos.html',list=l)

@app.route("/envios")
def verEnvios():
    l = []
    g = envios
    for s in g.subjects(predicate=RDF.type, object=envios_ns.type):
        dic = {}
        dic['idEnvio'] = g.value(subject = s, predicate= envios_ns.Id)
        dic['Estado del envio'] = g.value(subject = s, predicate= envios_ns.EstadoEnvio)
        dic['Fecha de realizacion del envio'] = g.value(subject = s, predicate= envios_ns.Fecharealizacion)
        dic['Direccion de entrega'] = g.value(subject = s, predicate= envios_ns.Tienedirecciondeentrega)
        dic['idPedido'] = g.value(subject = s, predicate = envios_ns.Llevaacabo)
        l = l + [dic]
        
    return render_template('envios.html', list=l)

@app.route("/envios/<id>/productos", methods=['GET']) 
def verProductosEnvio(id):
    l = []
    g = envios
    dic = {}
        # Anadimos los atributos que queremos renderizar a la vista
    prods = []
    container = g.value(subject=envios_ns[id],predicate=envios_ns.Contiene)
    c = Collection(g,container)
    dic['idEnvio'] = id
    idPedidoCompleto = g.value(subject=envios_ns[id],predicate=envios_ns.Llevaacabo)
    noVale, idPedido = idPedidoCompleto.split("#")
    dic['idPedido'] = idPedido
    for item in c:
        dic['idProducto'] = g.value(subject=item, predicate=productos_ns.Id)
        l = l + [dic]
    
    return render_template('productosEnvios.html', list=l)

@app.route("/envios/<idEnvio>/productos/<idPedido>/<idProducto>", methods=['GET'])
def crearDevolucion(idEnvio, idPedido, idProducto):
    return render_template('crearPeticionDevolucion.html',idEnvio=idEnvio, idPedido=idPedido, idProducto=idProducto)


@app.route("/envios/<idEnvio>/productos/<idPedido>/<idProducto>/devolver", methods=['GET'])        
def crearPeticionDevolucion(idEnvio, idPedido, idProducto):
    global envios
    razon = request.args['razon']
    id = str(random.getrandbits(64))
    devolucion = devoluciones_ns[id]
    g = Graph()
    g.add((devolucion,RDF.type, devoluciones_ns.type))
    g.add((devolucion,devoluciones_ns.Id, Literal(id)))
    g.add((devolucion,devoluciones_ns.TienePedido,pedidos_ns[idPedido]))
    g.add((devolucion,devoluciones_ns.TieneProducto,productos_ns[idProducto]))
    g.add((devolucion,devoluciones_ns.DevolucionEsDelUsuario,usuarios_ns[name]))
    g.add((devolucion,devoluciones_ns.RazonDevolucion, Literal(razon)))

    obj = createAction(AgenteUsuario,'crearDevolucion')

    g.add((obj, RDF.type, agn.DevolvedorPedirDevolucion))
    msg = build_message(g,
        perf=ACL.request,
        sender=AgenteUsuario.uri,
        content=obj)

    # Enviamos el mensaje a cualquier agente admisor
    res = send_message_any(msg,AgenteUsuario,DirectorioAgentes,agenteDevolvedor_ns.type)
    msg = 'No Aceptada'
    acceptada = res.value(devolucion,devoluciones_ns.Acceptada)
    if acceptada:
        empresa = res.value(devolucion,devoluciones_ns.EmpresaMensajeria)
        lugar = res.value(devolucion,devoluciones_ns.DireccionRetorno)
        msg = 'Devolver mediante: ' + empresa + ' al lugar: ' + lugar

        container = envios.value(subject=envios_ns[idEnvio],predicate=envios_ns.Contiene)
        c = Collection(envios,container)
        if len(c) == 1: c.clear()
        else: 
            toDelete = productos_ns[idProducto]
            del c[c.index(toDelete)]

    guardarGrafo(envios)

    return msg

@app.route("/opinar")
def verProductosaOpinar():
    g = productos_a_opinar
    l = []
    #Todos los productos tienen el predicado "type" a productos.type.
    #De esta forma los obtenemos con mas facilidad y sin consulta sparql
    #La funcoin subjects retorna los sujetos con tal predicado y objeto
    for s in g.subjects(predicate=RDF.type,object=productos_ns.type):
        # Anadimos los atributos que queremos renderizar a la vista
        dic = {}
        dic['nom'] = g.value(subject = s,predicate = productos_ns.Nombre)
        dic['id'] = g.value(subject = s,predicate = productos_ns.Id)
        l = l + [dic]

    #Renderizamos la vista
    return render_template('listaProductosaOpinar.html',list=l)

@app.route("/productosaOpinar/<id>/opinar", methods=['GET'])
def darOpinion(id):
    return render_template('darOpinion.html',id=id)

@app.route("/productosaOpinar/<id>/crearOpinion", methods=['GET'])
def crearOpinion(id):
    puntuacion = request.args['puntuacion']
    descripcion = request.args['descripcion']
    g = Graph()
    # Id de la opinion
    g.add((opiniones_ns[name+id], opiniones_ns.Id, Literal(name+id)))
    g.add((opiniones_ns[name+id], RDF.type, opiniones_ns.type))

    #Usuario que opina y producto opinados
    g.add((opiniones_ns[name+id], productos_ns.Essobre, productos_ns[id]))
    g.add((opiniones_ns[name+id], opiniones_ns.Escritapor, agenteUsuario_ns[name]))
    
    g.add((opiniones_ns[name+id], opiniones_ns.Puntuacion, Literal(puntuacion)))
    g.add((opiniones_ns[name+id], opiniones_ns.Descripcion, Literal(descripcion)))
   
    obj = createAction(AgenteUsuario,'darOpinion')

    g.add((obj, RDF.type, agn.DarOpinion))
    msg = build_message(g,
        perf=ACL.request,
        sender=AgenteUsuario.uri,
        content=obj)

    # Enviamos el mensaje a cualquier agente opinador
    send_message_any(msg,AgenteUsuario,DirectorioAgentes,agenteOpinador_ns.type)

    borrarNodoRec(productos_a_opinar,productos_ns[id])
    guardarGrafo(productos_a_opinar)

    return redirect("/opinar")


def enviarCarritoFalsoTienda():

    prioridad = 'Indefinida'
    direccion = 'Calle falsa 083'
    cp = '00000'

    pedido = Graph()
    pedido_id = str(random.getrandbits(64))
    pedido.add((pedidos_ns[pedido_id],RDF.type,pedidos_ns.type))
    pedido.add((pedidos_ns[pedido_id],pedidos_ns.Id,Literal(pedido_id)))
    pedido.add((pedidos_ns[pedido_id],pedidos_ns.Hechopor,agenteUsuario_ns[name]))
    pedido.add((pedidos_ns[pedido_id],pedidos_ns.Prioridad,Literal(prioridad)))
    pedido.add((pedidos_ns[pedido_id],pedidos_ns.Importetotal,Literal(500)))
    pedido.add((pedidos_ns[pedido_id], pedidos_ns.Fecharealizacion,Literal(getCurrentDate())))

    node =  pedidos_ns[pedido_id + '-listaProductos']

    pedido.add((pedidos_ns[pedido_id],pedidos_ns.Contiene,node))

    c = Collection(pedido,node)


    for p in carritoFalso.subjects(predicate=RDF.type,object=productos_ns.type):
        for i in range(int(carritoFalso.value(p,productos_ns.Cantidad))):
            idProd = carritoFalso.value(p,productos_ns.Id)
            prodGraph = Graph()
            idProductoPedido = str(random.getrandbits(64))
            productoPedido = productosPedido_ns[idProductoPedido]

            prodGraph.add((productoPedido,RDF.type,productosPedido_ns.type))
            prodGraph.add((productoPedido,productosPedido_ns.Id,Literal(idProductoPedido)))
            prodGraph.add((productoPedido,productosPedido_ns.AsociadoAlProducto,productos_ns[idProd]))

            pedido += prodGraph
            c.append(productoPedido)
    


    add_localizacion_node(pedido,pedidos_ns[pedido_id],pedidos_ns.Tienedirecciondeentrega,direccion,cp)

    #Enviar mensaje a la tienda
    enviarPedidoATienda(pedido)


@app.route("/stressTest")
def stressTest():
    ''' manda montones de peticiones de compra a la tienda '''
    j = 10
    try:
        j = request.args['n'] 
    except KeyError:
        pass

    for i in range(j):
        enviarCarritoFalsoTienda()

    return "Prueba de estres finalizada"

@app.route("/buscar")
def pag():
    """
    Entrada que sirve una pagina de web que cuenta hasta 10
    :return:
    """
    return render_template('buscarProductos.html')

@app.route("/comm")
def comunicacion():
    # Extraemos el mensaje y creamos un grafo con el
    cargarGrafos()
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)
    # Comprobamos que sea un mensaje FIPA ACL y que la performativa sea correcta
    if not msgdic:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = create_notUnderstood(AgenteUsuario,None)
    else:
        content = msgdic['content']
        # Averiguamos el tipo de la accion
        accion = gm.value(subject=content, predicate=RDF.type)

        #Llamada dinamica a la accion correspondiente
        if accion in actions:
            gr = actions[accion](gm)
        else:
            gr = create_notUnderstood(AgenteUsuario,None)

    return gr.serialize(format='xml')


@app.route("/buscarProductos", methods=['GET','POST'])
def buscarProductos():
    criterio = request.args['criterio']
    g = Graph()
    peticion_id = random.getrandbits(64)
    peticion = peticiones_ns[peticion_id]
    g.add((peticion, peticiones_ns.Busqueda, Literal(criterio)))
    g.add((peticion, peticiones_ns.Id, Literal(peticion_id)))
    g.add((peticion, peticiones_ns.User, AgenteUsuario.uri))
    g.add((peticion, RDF.type, peticiones_ns.type))
    obj = createAction(AgenteUsuario,'peticionBusqueda')

    g.add((obj, RDF.type, agn.peticionBusqueda))
    msg = build_message(g,
        perf=ACL.request,
        sender=AgenteUsuario.uri,
        content=obj)

    # Enviamos el mensaje a cualquier agente admisor
    res = send_message_any(msg,AgenteUsuario,DirectorioAgentes,agenteBuscador_ns.type)
    l = []
    #Todos los productos tienen el predicado "type" a productos.type.
    #De esta forma los obtenemos con mas facilidad y sin consulta sparql
    #La funcoin subjects retorna los sujetos con tal predicado y objeto
    for s in res.subjects(predicate=RDF.type,object=productos_ns.type):
        # Anadimos los atributos que queremos renderizar a la vista
        dic = {}
        dic['nombre'] = res.value(subject = s,predicate = productos_ns.Nombre)
        dic['id'] = res.value(subject = s,predicate = productos_ns.Id)
        dic['importe'] = res.value(subject = s,predicate = productos_ns.Importe)
        l = l + [dic]

    #Renderizamos la vista
    return render_template('resultadoBusqueda.html',criterio=criterio, list=l)

def rebreRecomanacions(graph):
    global recomendaciones
    save = Graph()
    for r in graph.subjects(predicate=RDF.type,object=productos_ns.type):
        save+=expandirGrafoRec(graph,r)

    recomendaciones += save
    guardarGrafo(recomendaciones)
    return create_confirm(AgenteUsuario,None)

def recibirProductosaOpinar(graph):
    global productos_a_opinar
    save = Graph()
    for r in graph.subjects(predicate=RDF.type,object=productos_ns.type):
        save+=expandirGrafoRec(graph,r)

    productos_a_opinar += save
    guardarGrafo(productos_a_opinar)
    return create_confirm(AgenteUsuario,None)
"""
def resultadoDevolucion(graph):
    l = []
    #Todos los productos tienen el predicado "type" a productos.type.
    #De esta forma los obtenemos con mas facilidad y sin consulta sparql
    #La funcoin subjects retorna los sujetos con tal predicado y objeto
    for s in res.subjects(predicate=RDF.type,object=devoluciones_ns.type):
        # Anadimos los atributos que queremos renderizar a la vista
        dic = {}
        dic['nom'] = res.value(subject = s,predicate = ont.Producto)
        dic['razon'] = res.value(subject = s,predicate = ont.Razon)
        dic['estado'] = res.value(subject = s,predicate = ont.Estado)
        l = l + [dic]
    return render_template('devoluciones.html',list=l)
"""

def registrarFacturaEnvio(graph):
    global envios
    envio = graph.subjects(predicate=RDF.type,object=envios_ns.type).next()
    envios += expandirGrafoRec(graph,envio)
    guardarGrafo(envios)
    return create_confirm(AgenteUsuario)

def registerActions():
    global actions
    actions[agn.RecomendarProductos] = rebreRecomanacions
    actions[agn.PedirOpiniones] = recibirProductosaOpinar
    actions[agn.FacturaEnvio] = registrarFacturaEnvio
    #actions[agn.resultadoBusqueda] = mostrarResultadoBusqueda

def init_agent():
    register_message(AgenteUsuario,DirectorioAgentes,agenteUsuario_ns.type)

def start_server():
    init_agent()
    registerActions()
    cargarGrafos()
    cargarCarritoFalso()
    app.run(host=host,port=port,debug=True)


if __name__ == "__main__":
    start_server()