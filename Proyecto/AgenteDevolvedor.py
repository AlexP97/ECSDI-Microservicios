# -*- coding: utf-8 -*-
from imports import *

__author__ = 'adrian'

argumentos = getArguments(my_port=8003)
#Direcciones hardcodeadas (propia)
host = argumentos['host']
port = argumentos['port']

centroLogistico = argumentos['name']

directorio_host = argumentos['dir_host']
directorio_port = argumentos['dir_port']

addr = argumentos['addr']

ont = Namespace('Ontologias/root-ontology.owl')
agn = getAgentNamespace()

devolvedor = getNamespace('AgenteDevolvedor')
monetario = getNamespace('AgenteMonetario')
usuario = getNamespace('AgenteUsuario')
#Objetos agente
AgenteDevolvedor = Agent('AgenteDevolvedor',devolvedor['generic'],formatDir(addr,port) + '/comm',None)
DirectorioAgentes = Agent('DirectorioAgentes',agn.Directory,formatDir(directorio_host,directorio_port) + '/comm',None)

devoluciones_ns = getNamespace('Devoluciones')
devoluciones_db = 'Datos/devoluciones.turtle'
devoluciones = Graph()

pedidos_ns = getNamespace('Pedidos')
pedidos_db = 'Datos/pedidos.turtle'
pedidos = Graph()

productos_ns = getNamespace('Productos')
productos_db = 'Datos/productos.turtle'
productos = Graph()

productospedido_ns = getNamespace('ProductosPedido')

# Flask stuff
app = Flask(__name__,template_folder="AgenteDevolvedor/templates")

#Acciones. Este diccionario sera cargado con todos los procedimientos que hay que llamar dinamicamente 
# cuando llega un mensaje
actions = {}

#Carga los grafoos rdf de los distintos ficheros
def cargarGrafos():
	global devoluciones
	global pedidos
	global productos
	devoluciones = Graph()
	pedidos = Graph()
	productos = Graph()
	if os.path.isfile(devoluciones_db):
		devoluciones.parse(devoluciones_db,format="turtle")
	if os.path.isfile(pedidos_db):
		pedidos.parse(pedidos_db,format="turtle")
	if os.path.isfile(productos_db):
		productos.parse(productos_db,format="turtle")
	

def guardarGrafo(g,file):
	g.serialize(file,format="turtle")  

def guardarGrafoDevoluciones():
	guardarGrafo(devoluciones,devoluciones_db) 

def guardarGrafoPedidos():
	guardarGrafo(pedidos,pedidos_db) 

def nuevaDevolucion(graph): 
	graph.serialize('test.turtle',format='turtle')
	return decidirDevolucion(graph,graph.subjects(predicate=RDF.type,object=devoluciones_ns.type).next())

def crearMensajeAfirmativo(devolucion):
	g = Graph()
	g += expandirGrafoRec(devoluciones,devolucion)
	g.set((devolucion,devoluciones_ns.Acceptada,Literal(True)))
   	return g
def crearMensajeNegativo(devolucion):
	g = Graph()
	g.set((devolucion,devoluciones_ns.Acceptada,Literal(False)))
   	return g

def decidirDevolucion(graph,devolucion):  

	razon = str(graph.value(devolucion,devoluciones_ns.RazonDevolucion))

	seAtiende = True

	if razon == "NoSatisface" and not comprobar15Dias(graph,devolucion): #TODO si hace mas de 15 dias desde la recepcion rechazarlo, si no aceptarlo
		seAtiende = False

	if seAtiende:
		registrarDevolucion(graph,devolucion)
		return crearMensajeAfirmativo(devolucion)
	else:
		return crearMensajeNegativo(devolucion)

def getFechaEnvioProducto(graph,devolucion):
	pedido = graph.value(devolucion,devoluciones_ns.TienePedido)
	producto = graph.value(devolucion,devoluciones_ns.TieneProducto)
	node = pedidos.value(pedido,pedidos_ns.Contiene)
	c = Collection(pedidos,node)
	for elem in c:
		prodPedido = pedidos.value(elem,productosPedido_ns.AsociadoAlProducto)
		estado = str(pedidos.value(elem,productosPedido_ns.Estado))
		if estado == 'Enviado' and prodPedido == producto:
			return pedidos.value(elem,productosPedido_ns.FechaEnvio)

def registrarDevolucion(graph,devolucion):
	global devoluciones
	razon = str(graph.value(devolucion,devoluciones_ns.RazonDevolucion))
	e = elegirEmpresaMensajeria(razon)
	empresa = e[0]
	dir = e[1]

	graph.set((devolucion,devoluciones_ns.EmpresaMensajeria,Literal(empresa)))
	graph.set((devolucion,devoluciones_ns.DireccionRetorno,Literal(dir)))
	graph.set((devolucion,devoluciones_ns.EstadoDevolucion,Literal('EnMarcha')))

	devoluciones += graph
	guardarGrafoDevoluciones()

def comprobar15Dias(graph,devolucion):
	current_date = getCurrentDate()
	d1 = stringToDate(current_date)
	d0 = stringToDate(getFechaEnvioProducto(graph,devolucion))
	delta = d1 - d0
	return int(delta.days) < 15

def elegirEmpresaMensajeria(razon): #elegir la empresa de mensajeria
	rand = random.randint(0,3)
	mensajeria = None
	direccion = None
	if rand == 0:
		mensajeria = "Correos"
	elif rand == 1:
		mensajeria = "Seur"
	elif rand == 2:
		mensajeria = "UPS"
	elif rand == 3:
		mensajeria = "ASM"

	if razon == "NoSatisface":
		direccion = "Revision"
	elif razon == "Defectuoso":
		direccion = "Vertedero"
	elif razon == "Equivocado":
		direccion = "Tienda"

	return [mensajeria,direccion]


@app.route("/verDevoluciones")
def getDevoluciones():
	global devoluciones
	global devoluciones_ns

	list = []
	for dev in devoluciones.subjects(RDF.type,devoluciones_ns.type):
		dict = {}
		dict['id'] = devoluciones.value(dev,devoluciones_ns.Id)
		dict['estado'] = str(devoluciones.value(dev,devoluciones_ns.EstadoDevolucion))
		dict['empesa'] = devoluciones.value(dev,devoluciones_ns.EmpresaMensajeria)
		dict['direccion'] = devoluciones.value(dev,devoluciones_ns.DireccionRetorno)
		dict['user_id'] = devoluciones.value(dev,devoluciones_ns.DevolucionEsDelUsuario)
		dict['producto_id'] = devoluciones.value(dev,devoluciones_ns.TieneProducto)
		dict['pedido_id'] = devoluciones.value(dev,devoluciones_ns.TienePedido)
		list += [dict]

	return render_template('lista_devoluciones.html', list = list)

def pedirReembolso(persona, importe):      #pedir al agente monetario el reembolso del importe del producto
	obj = createAction(AgenteDevolvedor,'pedirDevolucion')

	gcom = Graph()

	gcom.add((obj,RDF.type,agn.MonetarioPedirDevolucion))
	gcom.add((obj, pagos_ns.SeDevuelveAlUsuario, persona))
	gcom.add((obj, pagos_ns.Importe, Literal(importe)))

	msg = build_message(gcom,
		perf=ACL.request,
		sender=AgenteDevolvedor.uri,
		content=obj)

	# Enviamos el mensaje a cualquier agente monetario
	send_message_any(msg,AgenteDevolvedor,DirectorioAgentes,agenteMonetario_ns.type)
@app.route("/reembolsar")
def reembolsar():
	id = request.args['id']
	devolucion = devoluciones_ns[id]

	if str(devoluciones.value(devolucion,devoluciones_ns.EstadoDevolucion)) == 'Finalizado':
		raise Exception("La devoluciona ya ha finalizado")

	pedido = devoluciones.value(devolucion,devoluciones_ns.TienePedido)
	producto = devoluciones.value(devolucion,devoluciones_ns.TieneProducto)
	node = pedidos.value(pedido,pedidos_ns.Contiene)
	usuario = devoluciones.value(devolucion,devoluciones_ns.DevolucionEsDelUsuario)
	importe = 0

	c = Collection(pedidos,node)
	for elem in c:
		prodPedido = pedidos.value(elem,productosPedido_ns.AsociadoAlProducto)
		estado = str(pedidos.value(elem,productosPedido_ns.Estado))
		if estado == 'Enviado' and prodPedido == producto:
			pedidos.set((elem,productosPedido_ns.Estado,Literal('Devuelto')))
			importe = productos.value(prodPedido,productos_ns.Importe)
			break

	devoluciones.set((devolucion,devoluciones_ns.EstadoDevolucion,Literal('Finalizado')))

	guardarGrafoDevoluciones()
	guardarGrafoPedidos()
	pedirReembolso(usuario, importe)

	return redirect("/verDevoluciones")

@app.route("/comm")
def comunicacion():
	global actions
	global AgenteDevolvedor
	# Extraemos el mensaje y creamos un grafo con él
	cargarGrafos()
    
	message = request.args['content']
	gm = Graph()
	gm.parse(data=message)

	msgdic = get_message_properties(gm)
	# Comprobamos que sea un mensaje FIPA ACL y que la performativa sea correcta
	if not msgdic or msgdic['performative'] != ACL.request:
		# Si no es, respondemos que no hemos entendido el mensaje
		gr = create_notUnderstood(AgenteDevolvedor,None)
	else:
		content = msgdic['content']
		# Averiguamos el tipo de la accion
		accion = gm.value(subject=content, predicate=RDF.type)

		#Llamada dinamica a la accion correspondiente
		if accion in actions:
			gr = actions[accion](gm)
		else:
			gr = create_notUnderstood(AgenteDevolvedor,None)

	return gr.serialize(format='xml')



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

def init_agent():
	register_message(AgenteDevolvedor,DirectorioAgentes,devolvedor.type)

def registerActions():
	global actions
	actions[agn.DevolvedorPedirDevolucion] = nuevaDevolucion

@app.route("/test1")
def test1():
	# test que hace una devolucion del usuario "adrian" del producto "productoprueba1"
	# del pedido "pedidoprueba1" por el motivo "Defectuoso"
	global ont
	obj = createAction(AgenteDevolvedor,'nuevaDevolucion')
	gcom = Graph()
	gcom.add((obj,RDF.type,agn.DevolvedorPedirDevolucion))
	
	gcom.add((ont.Devolucion, ont.Pedido, Literal("pedidoprueba1")))    #el objeto debera ser el identificador del pedido
	gcom.add((ont.Devolucion, ont.Producto, Literal("productoprueba1")))    #el objeto debera ser el identificador del producto en un pedido
	gcom.add((ont.Devolucion, ont.Usuario, Literal("adrian")))
	gcom.add((ont.Devolucion, ont.RazonDevolucion, Literal("Defectuoso")))

	msg = build_message(gcom,
		perf=ACL.request,
		sender=AgenteDevolvedor.uri,
		content=obj)
	send_message_any(msg,AgenteDevolvedor,DirectorioAgentes,devolvedor.type)

	return 'Exit'

@app.route("/test2")
def test2():
	# test que hace una devolucion del usuario "alex" del producto "productoprueba2"
	# del pedido "pedidoprueba2" por el motivo "NoSatisface"
	global ont
	obj = createAction(AgenteDevolvedor,'nuevaDevolucion')
	gcom = Graph()
	gcom.add((obj,RDF.type,agn.DevolvedorPedirDevolucion))
	
	gcom.add((ont.Devolucion, ont.Pedido, Literal("pedidoprueba2")))    #el objeto debera ser el identificador del pedido
	gcom.add((ont.Devolucion, ont.Producto, Literal("productoprueba2")))    #el objeto debera ser el identificador del producto en un pedido
	gcom.add((ont.Devolucion, ont.Usuario, Literal("alex")))
	gcom.add((ont.Devolucion, ont.RazonDevolucion, Literal("NoSatisface")))

	msg = build_message(gcom,
		perf=ACL.request,
		sender=AgenteDevolvedor.uri,
		content=obj)
	send_message_any(msg,AgenteDevolvedor,DirectorioAgentes,devolvedor.type)

	return 'Exit'

if __name__ == "__main__":
	# Ponemos en marcha los behaviors
	

	registerActions()

	cargarGrafos()
	init_agent()
	# Ponemos en marcha el servidor
	app.run(host=host, port=port, debug=True)

	print('The End')