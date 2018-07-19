# -*- coding: utf-8 -*-
from imports import * 

__author__ = 'adrian'


argumentos = getArguments(my_port=8006)

host = argumentos['host']
port = argumentos['port']

name = argumentos['name']

directorio_host = argumentos['dir_host']
directorio_port = argumentos['dir_port']

addr = argumentos['addr']

#Cambiamos la ruta por defecto de los templates para que sea dentro de los ficheros del agente
app = Flask(__name__,template_folder="AgenteVendedorExterno/templates")

#Espacio de nombres para los productos y los agentes
agn = getAgentNamespace()

AgenteMonetario = Agent('AgenteMonetario',agenteMonetario_ns[name],formatDir(addr,port) + '/comm',None)

actions = {}

DirectorioAgentes = Agent('DirectorioAgentes',agn.Directory,formatDir(directorio_host,directorio_port) + '/comm',None)

personas = Graph()
personas_db = 'Datos/personas.turtle'

def cargarGrafos():
    global personas
    personas = Graph()
    if os.path.isfile(personas_db):
        personas.parse(personas_db,format="turtle")


def guardarGrafo(g,file):
    g.serialize(file,format="turtle")   

def guardarGrafoPersonas():
    guardarGrafo(personas,personas_db)


def init_agent():
    register_message(AgenteMonetario,DirectorioAgentes,agenteMonetario_ns.type)
    cargarGrafos()

@app.route("/comm")
def comunicacion():
    global actions
    global AgenteMonetario
    cargarGrafos()
    
    # Extraemos el mensaje y creamos un grafo con él
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    # Comprobamos que sea un mensaje FIPA ACL y que la performativa sea correcta
    if not msgdic:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = create_notUnderstood(AgenteMonetario,None)
    else:
        content = msgdic['content']
        # Averiguamos el tipo de la accion
        accion = gm.value(subject=content, predicate=RDF.type)

        #Llamada dinamica a la accion correspondiente
        if accion in actions:
            gr = actions[accion](gm)
        else:
            gr = create_notUnderstood(AgenteMonetario,None)

    return gr.serialize(format='xml')

def getIBANvendedor(vendedor):
    return personas.value(subject=vendedor,predicate=vendedores_ns.IBAN)

def getTarjetaUsuario(usuario):
    return personas.value(subject=usuario,predicate=usuarios_ns.Tarjeta)

def getIBANtienda():
    return 'ABCD123456789'

def crearGrafoTransaccion(origen,destinatario,formaOrigen,formaDestinatario,importe):
    id = random.getrandbits(64)
    tr = transacciones_ns[str(id)]

    # Pagamos al vendedor mediante el servicio de pago
    obj = createAction(AgenteMonetario,'transaccion')

    gcom = Graph()
    gcom.add((obj,RDF.type,agn.MonetarioPedirPago))

    gcom.add((tr,RDF.type,transacciones_ns.type))
    gcom.add((tr, transacciones_ns.Id,Literal(id)))
    gcom.add((tr, transacciones_ns.Origen,Literal(origen)))
    gcom.add((tr, transacciones_ns.Destinatario,Literal(destinatario)))
    gcom.add((tr, transacciones_ns.FormaOrigen,Literal(formaOrigen)))
    gcom.add((tr, transacciones_ns.FormaDestino,Literal(formaDestinatario)))
    gcom.add((tr, transacciones_ns.Importe,Literal(importe)))

    return build_message(gcom,perf=ACL.request,sender=AgenteMonetario.uri,content=obj)

def pedirPagoTiendaExterna(graph):
    #Miramos el vendedor que nos ocupa
    cargarGrafos()
    parent = graph.subjects(RDF.type,agn.MonetarioPedirPagoTiendaExterna).next()

    vendedor = graph.value(parent,pagos_ns.SePagaALaTienda)
    importe = graph.value(parent,pagos_ns.Importe)

    destinatario = getIBANvendedor(vendedor)
    origen = getIBANtienda()
    formaDestinatario = 'IBAN'
    formaOrigen = 'IBAN'
    
    msg = crearGrafoTransaccion(origen,destinatario,formaOrigen,formaDestinatario,importe)

    # Enviamos el mensaje a cualquier agente admisor
    send_message_any(msg,AgenteMonetario,DirectorioAgentes,agenteServicioPago_ns.type)

    return create_confirm(AgenteMonetario,None)

def pedirDevolucion(graph):
    #Miramos el vendedor que nos ocupa
    cargarGrafos()
    parent = graph.subjects(RDF.type,agn.MonetarioPedirDevolucion).next()

    usuario = graph.value(parent,pagos_ns.SeDevuelveAlUsuario)
    importe = graph.value(parent,pagos_ns.Importe)

    destinatario = getTarjetaUsuario(usuario)
    origen = getIBANtienda()
    formaDestinatario = 'Tarjeta'
    formaOrigen = 'IBAN'
    
    msg = crearGrafoTransaccion(origen,destinatario,formaOrigen,formaDestinatario,importe)

    # Enviamos el mensaje a cualquier agente admisor
    send_message_any(msg,AgenteMonetario,DirectorioAgentes,agenteServicioPago_ns.type)

    return create_confirm(AgenteMonetario,None)

def pedirPagoPedido(graph):
    cargarGrafos()
    #Miramos el vendedor que nos ocupa
    parent = graph.subjects(RDF.type,agn.MonetarioPedirPagoPedido).next()

    usuario = graph.value(parent,pagos_ns.SeHaceA)
    importe = graph.value(parent,pagos_ns.Importe)

    destinatario = getIBANtienda()
    origen = getTarjetaUsuario(usuario)
    formaDestinatario = 'IBAN'
    formaOrigen = 'Tarjeta'
    
    msg = crearGrafoTransaccion(origen,destinatario,formaOrigen,formaDestinatario,importe)

    # Enviamos el mensaje a cualquier agente admisor
    send_message_any(msg,AgenteMonetario,DirectorioAgentes,agenteServicioPago_ns.type)

    return create_confirm(AgenteMonetario,None)


@app.route("/Stop")
def stop():
    """
    Entrypoint que para el agente
    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"


def tidyup():
    """
    Acciones previas a parar el agente
    """
    global cola1
    cola1.put(0)
    pass

def registerActions():
    global actions
    actions[agn.MonetarioPedirPagoPedido] = pedirPagoPedido
    actions[agn.MonetarioPedirPagoTiendaExterna] = pedirPagoTiendaExterna
    actions[agn.MonetarioPedirDevolucion] = pedirDevolucion

if __name__ == "__main__":
    registerActions()
    init_agent()
    # Ponemos en marcha el servidor
    app.run(host=host, port=port, debug=True)
