# -*- coding: utf-8 -*-
from imports import *

__author__ = 'joan'

argumentos = getArguments(my_port=8010)
#Direcciones hardcodeadas (propia)
host = argumentos['host']
port = argumentos['port']

#Nombre del vendedor externo. Servira para generar una URI de recurso 
#Aun asi es probable que solo utilitzemos 1 vendedor
nombre = argumentos['name']

directorio_host = argumentos['dir_host']
directorio_port = argumentos['dir_port']

addr = argumentos['addr']

#Carga el grafo rdf del fichero graphFile
def cargarGrafo(graph):
	g = Graph()
	if os.path.isfile(graphFile):
		g.parse(graphFile,format="turtle")
	return g



#Cambiamos la ruta por defecto de los templates para que sea dentro de los ficheros del agente
app = Flask(__name__,template_folder="AgenteVendedorExterno/templates")
#Espacios de nombres utilizados
#Espacio de los agentes en general
agn = getAgentNamespace()

#Espacio de nombres del vendedor y del admisor (aqui se guardan acciones y demas historias)
vendedor = getNamespace('AgenteVendedorExterno')
admisor = getNamespace('AgenteAdmisor')

#Objetos agente, no son necesarios en toda regla pero sirven para agilizar comunicaciones
AgenteVendedorExterno = Agent('AgenteVendedorExterno',vendedor[nombre],formatDir(addr,port) + '/comm',None)
DirectorioAgentes = Agent('DirectorioAgentes',agn.Directory,formatDir(directorio_host,directorio_port) + '/comm',None)
#Cargar el grafo de datos
graphFile = 'AgenteVendedorExterno/' + nombre + '.turtle'
#Espacio de nombres para el modelo de productos
productos = getNamespace('Productos')

#Acciones. Este diccionario sera cargado con todos los procedimientos que hay que llamar dinamicamente 
# cuando llega un mensaje
actions = {}

#cargamos el grafo
g = cargarGrafo(graphFile)

def init_agent():
	register_message(AgenteVendedorExterno,DirectorioAgentes,vendedor.type)

def getNombreVendedor():
	return nombre

def registrarResponsabilidadEnvio(graph):
	global g
	'''
	comunicacion iniciada por el agente receptor
	Indica si el envio corre a cabo de nosotros mismos o de la tienda. 
	Si es a cabo de nosotros nos informaran de los datos de la entrega,
	aunque no haremos mucho con ellos
	'''
	pedido = graph.subjects(predicate=RDF.type,object=getNamespace('Pedidos').type).next()
	subgraph = expandirGrafoRec(graph,pedido)
	g += subgraph
	guardarGrafo()

	return create_confirm(AgenteVendedorExterno,None)

@app.route("/")
def main_page():
	"""
	Pagina principal. Contiene un menu muy simple
	"""
	return render_template('main.html')



@app.route("/comm")
def comunicacion():

	# Extraemos el mensaje y creamos un grafo con él
	message = request.args['content']
	gm = Graph()
	gm.parse(data=message)

	msgdic = get_message_properties(gm)
	# Comprobamos que sea un mensaje FIPA ACL y que la performativa sea correcta
	if not msgdic or msgdic['performative'] != ACL.inform:
		# Si no es, respondemos que no hemos entendido el mensaje
		gr = create_notUnderstood(AgenteVendedorExterno,None)
	else:
		content = msgdic['content']
		# Averiguamos el tipo de la accion
		accion = gm.value(subject=content, predicate=RDF.type)

		#Llamada dinamica a la accion correspondiente
		if accion in actions:
			gr = actions[accion](gm)
		else:
			gr = create_notUnderstood(AgenteVendedorExterno,None)

	return gr.serialize(format='xml')


@app.route("/verProductos")
def verProductos():
	"""
	Pagina de productos. Contiene una tabla y poco mas.
	Los productos no tienen estados asociados ya que suponemos que siempre hay stock
	"""
	l = []
	#Todos los productos tienen el predicado "type" a productos.type.
	#De esta forma los obtenemos con mas facilidad y sin consulta sparql
	#La funcoin subjects retorna los sujetos con tal predicado y objeto
	for s in g.subjects(predicate=RDF.type,object=productos.type):
		l+=[producto_a_dict(g,s)]

	#Renderizamos la vista
	return render_template('listaProductos.html',list=l)

@app.route("/verPedidos")
def verPedidos():
	#TODO
	"""
	Pagina de pedidos. Se pueden ver que pedidos han sido realizados.
	Tambien se puede ver en que estado se encuentran los pedidos y de quien es la responsabilidad
	Responsabilidad: Nuestra o de la tienda
	Estado: En curso, Enviado
	"""
	pedidos = g.subjects(predicate=RDF.type,object=getNamespace('Pedidos').type)
	l = []
	for p in pedidos:
		d = pedido_a_dict(g,p)
		mi_tienda = vendedor[nombre]
		d['mi_responsabilidad'] = g.value(subject=p,predicate=getNamespace('Pedidos').VendedorResponsable) == mi_tienda or False
		l+=[d]


	return render_template('listaPedidos.html',list=l)

@app.route("/productos/<id>/nuevoCentro")
def nuevoCentro(id):
	return render_template('nuevoCentro.html',id=id)


@app.route("/productos/<id>/crearCentroProducto")
def crearCentro(id):
	productos_ns = getNamespace('Productos')
	centros_ns = getNamespace('Centros')

	producto = getNamespace('Productos')[id]

	centro = centros_ns[request.args['centro_id']]
	g.add((centro,centros_ns.Id,Literal(request.args['centro_id'])))

	node = g.value(subject=producto,predicate=productos_ns.CentrosLogisticos) or productos_ns[id + '-listaCentros']

	g.add((producto,productos_ns.CentrosLogisticos,node))

	c = Collection(g,node)
	c.append(centro)

	guardarGrafo()
	
	return redirect('/verProductos')

def cobrarEnvio(user,importe):
	gcom = Graph()

	obj = createAction(AgenteVendedorExterno,'cobrarPedido')

	

	gcom.add((obj, RDF.type, agn.MonetarioPedirPagoPedido))
	gcom.add((obj, pagos_ns.SeHaceA, user))
	gcom.add((obj, pagos_ns.Importe,Literal(importe)))
	# Lo metemos en un envoltorio FIPA-ACL y lo enviamos
	msg = build_message(gcom,
		perf=ACL.inform,
		sender=AgenteVendedorExterno.uri,
		content=obj)

	# Enviamos el mensaje a cualquier agente monetario
	send_message_any(msg,AgenteVendedorExterno,DirectorioAgentes,agenteMonetario_ns.type)

@app.route("/enviarPedido")
def enviarPedido():
	""" 
	Representa el envio de un pedido que era responsabilidad del vendedor externo.	
	Se accede a esta accion normalmente a traves de la vista de pedidos 
	"""
	global g
	id = request.args['id']
	vendedor = g.value(subject=pedidos_ns[id],predicate=pedidos_ns.VendedorResponsable)
	user = g.value(subject=pedidos_ns[id],predicate=pedidos_ns.Hechopor)
	importe = g.value(subject=pedidos_ns[id],predicate=pedidos_ns.Importetotal)

	cobrarEnvio(user,importe)

	g.remove((pedidos_ns[id],pedidos_ns.VendedorResponsable,None))
	guardarGrafo()
	return redirect("/")


@app.route("/anadir")
def nuevoProducto():
	"""
	Mostrar pagina para poner un producto a la venda
	"""
	return render_template('nuevoProducto.html')

@app.route("/borrar")
def borrarProducto():
	''' 
	Borra el producto de la base de datos local
	'''
	id = request.args['id']
	g.remove((productos[id],None,None))
	guardarGrafo()
	return redirect("/verProductos")


@app.route("/crearProducto", methods=['GET'])
def crearProducto():
	'''
	Crea un producto SOLO en local. No envia nada a la tienda.
	'''
	crearProducto(request.args)
	return redirect("/verProductos")

@app.route("/poner_venta", methods=['GET'])
def ponerVenda():
	'''
	Pone un producto en local en venta. Se comunica con la tienda
	'''
	#Pillamos la id del recurso 
	id = request.args['id']

	#Hacemos una subseleccion del grafo con solo el producto a enviar
	producto = expandirGrafoRec(g,productos[id])
	gcom = Graph()
	gcom+=producto

	#Esta variable sirve para poca cosa, se podria utilizar cualquier nombre en teoria
	obj = createAction(AgenteVendedorExterno,'nuevoProducto')
	#La variable mas importante es el tipo de accion. Esto se enlaza en esta linea. 
	# Utilizaremos el espacio de nombres agn para referenciar acciones 
	# porque es global a todos los agentes de la tienda
	# Lo que el admisor interpretara sera el agn.VendedorNuevoProducto
	gcom.add((obj, RDF.type, agn.VendedorNuevoProducto))
	# Lo metemos en un envoltorio FIPA-ACL y lo enviamos
	msg = build_message(gcom,
		perf=ACL.request,
		sender=AgenteVendedorExterno.uri,
		content=obj)

	# Enviamos el mensaje a cualquier agente admisor
	send_message_any(msg,AgenteVendedorExterno,DirectorioAgentes,admisor.type)

	#Si todo ha ido correctamente podemos marcar el producto como en venta
	g.set((productos[id],productos.enVenta,Literal(True)))
	return redirect("/")

@app.route("/stop")
def stop():
	"""
	Entrypoint que para el agente

	:return:
	"""
	tidyup()
	shutdown_server()
	return "Parando Servidor"

def crearProducto(attrs):

	#Agarramos los atributos del request http
	nombre = attrs['nombre']
	id = attrs['id']
	precio = attrs['precio']

	#Insertamos todos las relaciones del producto. Notese que tambien tenemos que incorporar 
	#el RDF.type para que sea mas facil consultar sobre los productos mas adelante.
	#Tambien metemos nuestra propia URI de vendedor como Esvendidopor, asi agilizamos el proceso de relacion
	#productos[id] crea un recurso con el url del namespace "productos" seguido del identificador
	g.add((productos[id],productos.Nombre,Literal(nombre)))
	g.add((productos[id],productos.Importe,Literal(precio)))
	g.add((productos[id],productos.Id,Literal(id)))
	g.add((productos[id],productos.enVenta,Literal(False)))
	g.add((productos[id],RDF.type,productos.type))
	g.add((productos[id],productos.Esvendidopor,agenteVendedor_ns[getNombreVendedor()]))


	guardarGrafo()

def guardarGrafo():
	g.serialize(graphFile,format="turtle")	

def registerActions():
	global actions
	actions[agn.ReceptorInformarResponsabilidad] = registrarResponsabilidadEnvio



def tidyup():
	#Instrucciones de parada
	guardarGrafo()

def start_server():
	init_agent()
	registerActions()
	app.run(host=host,port=port,debug=True)


if __name__ == "__main__":
	start_server()

