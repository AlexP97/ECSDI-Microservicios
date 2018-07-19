
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 15:58:13 2013

Esqueleto de agente usando los servicios web de Flask

/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente

Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente

Asume que el agente de registro esta en el puerto 9000

@author: javier
"""

from imports import *

__author__ = 'joan'

argumentos = getArguments(my_port=8008)
#Direcciones hardcodeadas (propia)
host = argumentos['host']
port = argumentos['port']

name = argumentos['name']

directorio_host = argumentos['dir_host']
directorio_port = argumentos['dir_port']

addr = argumentos['addr']

agn = getAgentNamespace()

#Objetos agente
AgenteReceptor = Agent('AgenteReceptor',agenteReceptor_ns[name],formatDir(addr,port) + '/comm',None)
DirectorioAgentes = Agent('DirectorioAgentes',agn.Directory,formatDir(directorio_host,directorio_port) + '/comm',None)


productos_db = 'Datos/productos.turtle'
productos = Graph()

pedidos_db = 'Datos/pedidos.turtle'
pedidos = Graph()

centros_db = 'Datos/centros.turtle'
centros = Graph()


cola1 = Queue()

# Flask stuff
app = Flask(__name__,template_folder="AgenteReceptor/templates")

#Acciones. Este diccionario sera cargado con todos los procedimientos que hay que llamar dinamicamente 
# cuando llega un mensaje
actions = {}

def initAgent():
	register_message(AgenteReceptor,DirectorioAgentes,agenteReceptor_ns.type)
#Carga los grafoos rdf de los distintos ficheros
def cargarGrafos():
	global productos
	global pedidos
	productos = Graph()
	pedidos = Graph()
	if os.path.isfile(productos_db):
		productos.parse(productos_db,format="turtle")
	if os.path.isfile(pedidos_db):
		pedidos.parse(pedidos_db,format="turtle")
	if os.path.isfile(centros_db):
		centros.parse(centros_db,format="turtle")

def guardarGrafo(g,file):
	g.serialize(file,format="turtle")	

def guardarGrafoPedidos():
	pedidos.serialize(pedidos_db,format="turtle")


@app.route("/comm")
def comunicacion():

	cargarGrafos()
    
	# Extraemos el mensaje y creamos un grafo con él
	message = request.args['content']
	gm = Graph()
	gm.parse(data=message)

	msgdic = get_message_properties(gm)

	# Comprobamos que sea un mensaje FIPA ACL y que la performativa sea correcta
	if not msgdic:
		# Si no es, respondemos que no hemos entendido el mensaje
		gr = create_notUnderstood(AgenteReceptor,None)
	else:
		content = msgdic['content']
		# Averiguamos el tipo de la accion
		accion = gm.value(subject=content, predicate=RDF.type)

		#Llamada dinamica a la accion correspondiente
		if accion in actions:
			gr = actions[accion](gm)
		else:
			gr = create_notUnderstood(AgenteReceptor,None)

	return gr.serialize(format='xml')


@app.route("/")
def main():
	"""
	Pagina principal. Contiene un menu muy simple
	"""
	return render_template('main.html')

@app.route("/info")
def info():
	list = [productos,pedidos]
	list = [g.serialize(format="turtle") for g in list]
	return render_template("info.html",list=list)

@app.route("/anadir")
def anadirPedido():
	''' Muestra la pagina de anadir un nuevo pedido '''
	return render_template('nuevoPedido.html')



@app.route("/verPedidos")
def verPedidos():
	list = []

	#obtenemos todos los pedidos de la tienda
	pds = pedidos.subjects(predicate=RDF.type,object=pedidos_ns.type)

	for p in pds:
		dict = pedido_a_dict(pedidos,p)
		list+= [dict]

	return render_template('listaPedidos.html',list=list)

@app.route("/crearPedido")
def crearPedido():
	'''
	Crear un pedido mediante los atributos que se mandan en el http request
	'''
	dict = request.args
	g = dict_a_pedido(dict)
	global pedidos
	pedidos+=g
	guardarGrafo(pedidos,pedidos_db)

	return redirect("/")

@app.route("/pedidos/<id>/anadirProductoPedido")
def anadirProductoPedido(id):
	'''
	crea la vista para anadir un producto a un pedido en concreto
	'''
	return render_template('nuevoProductoPedido.html',id=id)

@app.route("/pedidos/<id>/crearProductoPedido")
def crearProductoPedido(id):
	''' anade un producto a un pedido en especifico '''
	global pedidos
	pedido = pedidos_ns[id]

	producto_id = request.args['id']
	estado = request.args['estado']
	fechaEnvio = request.args['fechaEnvio']

	g = Graph()
	prod_parent = productos_ns[producto_id]
	g.add((prod_parent,RDF.type,productos_ns.type))
	g.add((prod_parent,productos_ns.Id,Literal(producto_id)))
	g.add((prod_parent,productos_ns.EstadoProducto,Literal(estado)))
	g.add((prod_parent,productos_ns.Fechaenvio,Literal(fechaEnvio)))

	pedidos += g

	node =  productos.value(subject=pedido,predicate=pedidos_ns.Contiene) or pedidos_ns[id + '-listaProductos']

	#node = productos.objects(subject=pedido,predicate=pedidos_ns.Contiene).next() or BNode()
	pedidos.add((pedido,pedidos_ns.Contiene,node))
	c = Collection(pedidos,node)
	c.append(prod_parent)
	#Modificar la coleccion de productos del pedido
	guardarGrafoPedidos()
	return redirect("/verPedidos")

@app.route("/pedidos/<id>/verProductos")
def verProductosPedido(id):

	# Busca toda la informacion que cuelga de pedidos
	pedido = expandirGrafoRec(pedidos,pedidos_ns[id])


@app.route("/simularPedido")
def simularPedido():
	'''
	simula un pedido que ha llegado a la tienda. Utiliza el propio pedido
	notifica a la tienda externa que el pedido sera llevado a cabo por ellos
	'''
	id = request.args['id']
	pedido = pedidos_ns[id]
	decidirResponsabilidadEnvio(pedido)
	return redirect("/verPedidos")

def enviarPagoVendedorExterno(pedido):
	# cal enviar el id del vendedor i el import, res mes
	vendedorId = pedidos.value(pedido,pedidos_ns.VendedorResponsable)
	importe = pedidos.value(pedido,pedidos_ns.Importetotal)

	g = Graph()
	obj = createAction(AgenteReceptor,'pagoExterno')
	g.add((obj, RDF.type, agn.MonetarioPedirPagoTiendaExterna))
	g.add((obj, pagos_ns.SePagaALaTienda, vendedorId))
	g.add((obj, pagos_ns.Importe,Literal(importe)))
	# Lo metemos en un envoltorio FIPA-ACL y lo enviamos
	msg = build_message(g,
		perf=ACL.inform,
		sender=AgenteReceptor.uri,
		content=obj)

	# Enviamos el mensaje a cualquier agente admisor
	send_message_any(msg,AgenteReceptor,DirectorioAgentes,agenteMonetario_ns.type)

def procesarDecision(pedido,responsabilidad):
	responsable = responsabilidad['responsabilidad']

	if responsable:
		#Hay que asignar el respnsable al pedido
		pedidos.add((pedido,pedidos_ns.VendedorResponsable,responsabilidad['vendedores'][0]))
		enviarPagoVendedorExterno(pedido)

	#Preparamos el mensaje
	pedido = expandirGrafoRec(pedidos,pedido)
	obj = createAction(AgenteReceptor,'informarResponsabilidad')
	#Anadimos la accion del mensaje
	pedido.add((obj,RDF.type,agn.ReceptorInformarResponsabilidad))
	#Indicamos si el receptor es el responsable o no del pedido
	msg = build_message(pedido,
		perf=ACL.inform,
		sender=AgenteReceptor.uri,
		content=obj)

	send_message_set(msg,AgenteReceptor,DirectorioAgentes,agenteVendedor_ns.type,responsabilidad['vendedores'])
	guardarGrafoPedidos()

def productoPerteneceTiendaExterna(producto):
	vendedor = productos.value(subject=producto,predicate=productos_ns.Esvendidopor)
	if (vendedor): return vendedor
	else: return False

def decidirResponsabilidad(pedido):
	'''
	Devuelve True si el envio es responsabilidad del vendedor externo
	Devuelve False si el envio es responsabilidad de la tienda
	'''
	container = pedidos.value(subject=pedido,predicate=pedidos_ns.Contiene)
	c = Collection(pedidos,container)
	vendedores = []
	pertenecen = 0
	i = 0
	for item in c:
		#Iteramos los productos del pedido
		producto = pedidos.value(subject=item,predicate=productosPedido_ns.AsociadoAlProducto)
		vendedor = productoPerteneceTiendaExterna(producto)
		if (vendedor):
			vendedores += [vendedor]
			pertenecen += 1
		i+=1

	#Eliminamos los duplicados
	vendedores = list(set(vendedores))
	#Solo hay que asignar la responsabilidad al vendedor externo si este es el propietario 
	#De todos los productos del envio
	envioExterno = len(vendedores) == 1
	ret = {
		'responsabilidad':envioExterno,
		'vendedores':vendedores
	}
	return ret

def calcularImportePedido(graph,pedido):


	total = graph + productos
	suma = 0
	node = total.value(pedido,pedidos_ns.Contiene)

	c = Collection(total,node)

	for p in c:
		try:
			producto = total.value(subject=p,predicate=productosPedido_ns.AsociadoAlProducto)
			suma += int(total.value(subject=producto,predicate=productos_ns.Importe))
		except ValueError:
			#Si hay un importe mal formado ignoramos
			pass

	return suma

	

def registrarPedido(graph,pedido):
	''' registra un pedido en la base de datos de pedidos de la tienda '''
	''' hay que anadir los atributos extra al pedido '''
	global pedidos

	graph.add((pedido,pedidos_ns.Importetotal,Literal(calcularImportePedido(graph,pedido))))
	#No necesitamos el estado
	#graph.add((pedido,pedidos_ns.Estadodelpedido,Literal(estado)))

	pedidos += graph
	guardarGrafoPedidos()
	return pedido

def decidirResponsabilidadEnvio(pedido):
	responsabilidad = decidirResponsabilidad(pedido)
	procesarDecision(pedido,responsabilidad)


def resolverEnvio(graph):

	cargarGrafos()
	pedidos = graph.subjects(predicate=RDF.type,object=pedidos_ns.type)
	for p in pedidos:
		pedido = registrarPedido(expandirGrafoRec(graph,p),p)
		decidirResponsabilidadEnvio(pedido)
		organizarPedido(pedido)
	
	return create_confirm(AgenteReceptor)

def centroMasCercano(pedido,producto):
	''' Atencion, localizacion y centros logisticos son 2 nodos de los grafos pedidos y productos '''
	g = Graph()
	g += pedidos
	g += productos
	g += centros

	direcciones_ns = getNamespace('Direcciones')
	productos_ns = getNamespace('Productos')

	#Obtenemos la direccion de entrega del pedido
	loc = g.value(pedido,pedidos_ns.Tienedirecciondeentrega)
	dir = g.value(loc,direcciones_ns.Direccion)
	cp = g.value(loc,direcciones_ns.Codigopostal)

	nodoLista = g.value(producto,productos_ns.CentrosLogisticos)

	col  = Collection(g,nodoLista)

	#Busca el centro logistico mas cercano que a nuestro caso equivale al que tiene
	#Un codigo postal mas cercano al del pedido
	res = {}
	for c in col:
		loc = g.value(c,getNamespace('Centros').Ubicadoen)
		centro_cp = g.value(loc,getNamespace('Direcciones').Codigopostal)
		try:
			res[c] = abs(int(cp) - int(centro_cp))
		except Exception:
			''' la operacion ha fallado porque algun input no esta bien '''
			pass

	if len(res) > 0:
		masCercano = min(res)
	else:
		raise Exception("No se ha podido derivar ningun centro para el producto: " + producto)

	return masCercano


def informarCentroLogisticoEnvio(centro,pedido,listaProductos):
	#Pedidos y productos juntados para obtener mas facilmente los atributos
	graph = pedidos + productos
	envio = pedido_a_envio(graph,pedido,listaProductos)

	centro_id = centros.value(centro,centros_ns.Id)

	empaquetador_uri = agenteEmpaquetador_ns[centro_id]


	obj = createAction(AgenteReceptor,'nuevoEnvio')
	envio.add((obj, RDF.type, agn.ReceptorNuevoEnvio))
	# Lo metemos en un envoltorio FIPA-ACL y lo enviamos
	msg = build_message(envio,
		perf=ACL.inform,
		sender=AgenteReceptor.uri,
		content=obj)

	# Enviamos el mensaje a cualquier agente admisor
	send_message_uri(msg,AgenteReceptor,DirectorioAgentes,agenteEmpaquetador_ns.type,empaquetador_uri)

def registrarDecisionCentro(centro,pedido,listaProductos):
	node = pedidos.value(pedido,pedidos_ns.Contiene)
	c = Collection(pedidos,node)
	for prod in c:
		pedidos.set((prod,productosPedido_ns.CentroAsignado,centro))
		pedidos.set((prod,productosPedido_ns.Estado,Literal('Asignado')))

	guardarGrafoPedidos()

def organizarPedido(pedido):
	'''Busca que centros logisticos pueden resolver la peticion de envio '''
	nodo = pedidos.value(pedido,pedidos_ns.Contiene)

	col = Collection(pedidos,nodo)

	decision = {}
	#Itera los productos del pedido
	for c in col:
		producto = pedidos.value(subject=c,predicate=productosPedido_ns.AsociadoAlProducto)
		masCercano = centroMasCercano(pedido,producto)
		if masCercano in decision:
			decision[masCercano] += [producto]
		else:
			decision[masCercano] = [producto]


	for c in decision:
		registrarDecisionCentro(c,pedido,decision[c])
		informarCentroLogisticoEnvio(c,pedido,decision[c])


@app.route("/simularOrganizar")
def simulacionOrganizar():
	id = request.args['id']
	pedido = pedidos_ns[id]
	organizarPedido(pedido)
	return redirect("/")


def getTransportistaName(transportista):
	tr = Graph()
	tr.parse('Datos/personas.turtle',format="turtle")
	return tr.value(subject=transportista,predicate=transportistas_ns.NombreEmpresa)


def getListaProductosEnviados(graph,envio):
	nodo = graph.value(subject=envio,predicate=envios_ns.Contiene)
	c = Collection(graph,nodo)
	ret = []
	for p in c:
		ret += [p]

	return ret

def comprobarPagoVendedorExterno(vendedores,producto):
	# devuelve un importe
	vendedor = productos.value(producto,productos_ns.Esvendidopor)
	if vendedor is not None:
		if vendedor in vendedores: vendedores[vendedor] += float(productos.value(producto,productos_ns.Importe))
		else: vendedores[vendedor] = float(productos.value(producto,productos_ns.Importe))
	#Por si acaso es immutable
	return vendedores

def pagarVendedores(vendedores):
	for vendedor in vendedores:
		importe = vendedores[vendedor]

		gcom = Graph()

		obj = createAction(AgenteReceptor,'pagarProducto')

		gcom.add((obj, RDF.type, agn.MonetarioPedirPagoTiendaExterna))
		gcom.add((obj, pagos_ns.SePagaALaTienda, vendedor))
		gcom.add((obj, pagos_ns.Importe,Literal(importe)))
		# Lo metemos en un envoltorio FIPA-ACL y lo enviamos
		msg = build_message(gcom,
			perf=ACL.inform,
			sender=AgenteReceptor.uri,
			content=obj)

		# Enviamos el mensaje a cualquier agente monetario
		send_message_any(msg,AgenteReceptor,DirectorioAgentes,agenteMonetario_ns.type)


def registrarProductosEnviados(graph,pedido,envio,centro):
	global pedidos
	#Registra los productos del grafo de envio como ya enviados en el pedido y de paso informa al
	# monetario de que pague a la tienda externa en los casos indicados
	fechaEnvio = getCurrentDate()
	lista = getListaProductosEnviados(graph,envio)
	node = pedidos.value(pedido,pedidos_ns.Contiene)
	vendedores = {}
	c = Collection(pedidos,node)

	for productoPedido in c:
		producto = pedidos.value(subject=productoPedido,predicate=productosPedido_ns.AsociadoAlProducto)
		centro_producto = pedidos.value(subject=productoPedido,predicate=productosPedido_ns.CentroAsignado)
		if producto in lista and centro_producto == centro:
			pedidos.set((productoPedido,productosPedido_ns.Estado,Literal('Enviado')))
			pedidos.set((productoPedido,productosPedido_ns.FechaEnvio,Literal(fechaEnvio)))
			vendedores = comprobarPagoVendedorExterno(vendedores,producto)
			lista.remove(producto)

	pagarVendedores(vendedores)
	guardarGrafoPedidos()


def registrarImporteFinal(pedido,importeEnvio):
	importe = pedidos.value(pedido,pedidos_ns.Importetotal)
	importeFinal = float(importe) + float(importeEnvio)
	pedidos.set((pedido,pedidos_ns.ImporteFinal,Literal(importeFinal)))

def enviarFacturaUsuario(graph,envio,importeEnvio):
	graph.set((envio,envios_ns.ImporteEnvio,importeEnvio))

	gcom = Graph()

	obj = createAction(AgenteReceptor,'registrarFactura')

	#Direccion del usuario
	uri = graph.value(envio,envios_ns.Hechopor)

	gcom.add((obj, RDF.type, agn.FacturaEnvio))
	#Ponemos el envio que hemos realizado
	gcom += expandirGrafoRec(graph,envio)
	# Lo metemos en un envoltorio FIPA-ACL y lo enviamos
	msg = build_message(gcom,
		perf=ACL.inform,
		sender=AgenteReceptor.uri,
		content=obj)

	msg.serialize('test.turtle',format='turtle')
	# Enviamos el mensaje a cualquier agente monetario
	send_message_uri(msg,AgenteReceptor,DirectorioAgentes,agenteUsuario_ns.type,uri)

def confirmarEnvio(graph):
	#Registrar los productos del pedido como enviados
	#Generar un envio metiendole el importe final
	#Actualizar todos los productos de un pedido para que sus estados y mierdas correspondan (usar el centro)
	#Informar al servicio de pago de los productos que fuesen externos
	parent = graph.subjects(RDF.type, agn.EnviadorConfirmarEnvio).next()
	envio = graph.subjects(RDF.type, envios_ns.type).next()
	envioGraph = expandirGrafoRec(graph,envio)
	pedido = envioGraph.value(envio,envios_ns.Llevaacabo)
	importeEnvio = graph.value(parent,pedidos_ns.ImporteEnvio)
	transportista = graph.value(parent,pedidos_ns.LoTransporta)
	centro = graph.value(parent,pedidos_ns.CentroResponsable)

	registrarProductosEnviados(graph,pedido,envio,centro)
	registrarImporteFinal(pedido,importeEnvio)
	enviarFacturaUsuario(graph,envio,importeEnvio)
	
	guardarGrafoPedidos()
	return create_confirm(AgenteReceptor)

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
	pass


def agentbehavior1(cola):
	"""
	Un comportamiento del agente

	:return:
	"""
	pass


def registerActions():
	global actions
	#Procesado de peticiones del usuario de compra
	actions[agn.UsuarioNuevoPedido] = resolverEnvio
	actions[agn.EnviadorConfirmarEnvio] = confirmarEnvio

'''Percepciones'''
def peticionDeCompra(graph):
	pass


if __name__ == '__main__':
	# Ponemos en marcha los behaviors
	ab1 = Process(target=agentbehavior1, args=(cola1,))
	ab1.start()

	initAgent()
	registerActions()

	cargarGrafos()

	# Ponemos en marcha el servidor
	app.run(host=host, port=port,debug=True)

	# Esperamos a que acaben los behaviors
	ab1.join()
	print('The End')


