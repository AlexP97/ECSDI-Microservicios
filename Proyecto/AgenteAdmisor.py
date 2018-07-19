
# -*- coding: utf-8 -*-
from imports import *

__author__ = 'joan'

argumentos = getArguments(my_port=8001)

host = argumentos['host']
port = argumentos['port']

name = argumentos['name']

directorio_host = argumentos['dir_host']
directorio_port = argumentos['dir_port']

addr = argumentos['addr']

agn = getAgentNamespace()

#Objetos agente
AgenteAdmisor = Agent('AgenteAdmisor',agenteAdmisor_ns[name],formatDir(addr,port) + '/comm',None)
DirectorioAgentes = Agent('DirectorioAgentes',agn.Directory,formatDir(directorio_host,directorio_port) + '/comm',None)

productos_db = 'Datos/productos.turtle'
productos = Graph()

cola1 = Queue()

# Flask stuff
app = Flask(__name__,template_folder="AgenteAdmisor/templates")
#Acciones. Este diccionario sera cargado con todos los procedimientos que hay que llamar dinamicamente 
# cuando llega un mensaje
actions = {}

#Carga los grafoos rdf de los distintos ficheros
def cargarGrafos():
	global productos
	productos = Graph()
	if os.path.isfile(productos_db):
		productos.parse(productos_db,format="turtle")
	

def guardarGrafo(g,file):
	g.serialize(file,format="turtle")	

@app.route("/")
def hola():
	return "soy el agente admisor, hola!"

@app.route("/altaProducto")
def altaProducto():
	return 'ruta no definida'


def nuevoProducto(graph):
	#TODO hay que generar una lista de centros logisticos que tienen este producto (lo generamos aleatoreamente?)
	global productos
	p = graph.subjects(predicate=RDF.type,object=productos_ns.type)
	for pe in p:
		add = expandirGrafoRec(graph,pe)
		productos += add
	guardarGrafo(productos,productos_db)
	return create_confirm(AgenteAdmisor,None)


@app.route("/comm")
def comunicacion():

	cargarGrafos()
	# Extraemos el mensaje y creamos un grafo con él
	message = request.args['content']
	gm = Graph()
	gm.parse(data=message)

	msgdic = get_message_properties(gm)
	# Comprobamos que sea un mensaje FIPA ACL y que la performativa sea correcta
	if not msgdic or msgdic['performative'] != ACL.request:
		# Si no es, respondemos que no hemos entendido el mensaje
		gr = create_notUnderstood(AgenteAdmisor,None)
	else:
		content = msgdic['content']
		# Averiguamos el tipo de la accion
		accion = gm.value(subject=content, predicate=RDF.type)

		#Llamada dinamica a la accion correspondiente
		if accion in actions:
			gr = actions[accion](gm)
		else:
			gr = create_notUnderstood(AgenteAdmisor,None)

	return gr.serialize(format='xml')


@app.route("/info")
def info():
	list = [productos]
	list = [g.serialize(format="turtle") for g in list]
	return render_template("info.html",list=list)


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
	register_message(AgenteAdmisor,DirectorioAgentes,agenteAdmisor_ns.type)

def registerActions():
	global actions
	actions[agn.VendedorNuevoProducto] = nuevoProducto



if __name__ == '__main__':
	# Ponemos en marcha los behaviors
	ab1 = Process(target=agentbehavior1, args=(cola1,))
	ab1.start()

	registerActions()

	cargarGrafos()
	init_agent()
	# Ponemos en marcha el servidor
	app.run(host=host, port=port,debug=True)

	# Esperamos a que acaben los behaviors
	ab1.join()
	print('The End')


