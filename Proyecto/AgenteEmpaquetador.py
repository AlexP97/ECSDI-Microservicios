from imports import *
# Definimos los parametros de la linea de comandos

app = Flask(__name__,template_folder="AgenteEmpaquetador/templates")

__author__ = 'joan'

argumentos = getArguments(my_port=8004)
#Direcciones hardcodeadas (propia)
host = argumentos['host']
port = argumentos['port']

centroLogistico = argumentos['name']

directorio_host = argumentos['dir_host']
directorio_port = argumentos['dir_port']

addr = argumentos['addr']

agn = getAgentNamespace()

envios = Graph()
lotes = Graph()
pesos = Graph()

envios_db = 'Datos/Envios/%s.turtle'
lotes_db = 'Datos/Lotes/%s.turtle'
pesos_db = 'Datos/Pesos/%s.turtle'

#Objetos agente, no son necesarios en toda regla pero sirven para agilizar comunicaciones
AgenteEmpaquetador = Agent('AgenteEmpaquetador',getNamespace('AgenteEmpaquetador')[centroLogistico],formatDir(addr,port) + '/comm',None)
DirectorioAgentes = Agent('DirectorioAgentes',agn.Directory,formatDir(directorio_host,directorio_port) + '/comm',None)
#Cargar el grafo de datos

#Acciones. Este diccionario sera cargado con todos los procedimientos que hay que llamar dinamicamente
# cuando llega un mensaje
actions = {}

#Carga el grafo rdf del fichero graphFile
def cargarGrafos(centro):
	global envios,lotes,pesos
	envios = Graph()
	lotes = Graph()
	pesos = Graph()
	if os.path.isfile(envios_db%centro):
		envios.parse(envios_db%centro,format="turtle")
	if os.path.isfile(lotes_db%centro):
		lotes.parse(lotes_db%centro,format="turtle")
	if os.path.isfile(pesos_db%centro):
		pesos.parse(pesos_db%centro,format="turtle")

def guardarGrafoEnvios(centro):
	envios.serialize(envios_db%centro,format="turtle")

def guardarGrafoLotes(centro):
	lotes.serialize(lotes_db%centro,format="turtle")

def guardarGrafoPesos(centro):
	pesos.serialize(pesos_db%centro,format="turtle")

@app.route("/comm")
def comunicacion():
	# Extraemos el mensaje y creamos un grafo con el
	cargarGrafos(centroLogistico)
    
	message = request.args['content']
	gm = Graph()
	gm.parse(data=message)

	msgdic = get_message_properties(gm)
	gr = None
	# Comprobamos que sea un mensaje FIPA ACL y que la performativa sea correcta
	if not msgdic:
		# Si no es, respondemos que no hemos entendido el mensaje
		gr = create_notUnderstood(AgenteEmpaquetador,None)
	else:
		content = msgdic['content']
		# Averiguamos el tipo de la accion
		accion = gm.value(subject=content, predicate=RDF.type)

		#Llamada dinamica a la accion correspondiente
		if accion in actions:
			gr = actions[accion](gm)
		else:
			gr = create_notUnderstood(AgenteEmpaquetador,None)

	return gr.serialize(format='xml')



def calcularPesoEnvio(envio):

	# Juntamos los pesos para mas rapido acceso
	graph = envios + pesos

	lista = graph.value(envio,envios_ns.Contiene)

	productos  = Collection(graph,lista)

	#Anadimos las uris de los productos al envio y sumamos el importe total
	peso = 0
	for p in productos: 
		try:
			peso += int(graph.value(p,predicate=productos_ns.Peso))
		except ValueError:
			# Sumamos 0 al peso total
			pass

	return int(peso)

def crearLote(envio):
	peso = calcularPesoEnvio(envio)
	prioridad = envios.value(envio,envios_ns.Prioridad)

	#Generamos un id aleatorio
	lote_id = str(random.getrandbits(64))

	lote = lotes_ns[lote_id]

	lotes.add((lote,RDF.type,lotes_ns.type))
	lotes.add((lote,lotes_ns.Id,Literal(lote_id)))

	loc = envios.value(envio,envios_ns.Tienedirecciondeentrega)
	cp = envios.value(loc,direcciones_ns.Codigopostal)

	lotes.add((lote,lotes_ns.Ciudad,cp))
	#Hacemos que el lote este en reposo inicialmente
	lotes.add((lote,lotes_ns.Estadodellote,Literal("Idle")))
	#Anadimos el peso del lote
	lotes.add((lote,lotes_ns.Peso,Literal(peso)))
	#Prioridad del lote
	lotes.add((lote,lotes_ns.Prioridad,Literal(prioridad)))

	envioGraph = Graph()

	node = lotes.value(subject=lote,predicate=lotes_ns.TieneEnvios) or lotes_ns[lote_id + '-listaEnvios']

	lotes.add((lote,lotes_ns.TieneEnvios,node))

	c = Collection(lotes,node)

	c.append(envio)

	guardarGrafoLotes(centroLogistico)

def anadirEnvioLote(lote,envio):
	peso = calcularPesoEnvio(envio)

	try:
		peso += int(lotes.value(subject=lote,predicate=lotes_ns.Peso)) 
	except ValueError:
		#No sumar ningun peso. Esto no deberia ocurrir en situaciones normales
		pass
	#Sumamos el peso
	lotes.set((lote,lotes_ns.Peso,Literal(peso)))
	lotes.serialize('test.turtle',format='turtle')
	node = lotes.value(subject=lote,predicate=lotes_ns.TieneEnvios) or lotes_ns[lote_id + '-listaEnvios']

	c = Collection(lotes,node)

	c.append(envio)

	guardarGrafoLotes(centroLogistico)

def registrarEnvio(graph,envio):
	global envios
	envios += graph
	peso = calcularPesoEnvio(envio)
	#Anadimos el peso total del envio
	envios.add((envio,envios_ns.Peso,Literal(peso)))
	guardarGrafoEnvios(centroLogistico)

def combinarLotes(envio):
	loc = envios.value(envio,envios_ns.Tienedirecciondeentrega)
	cp = envios.value(loc,getNamespace('Direcciones').Codigopostal)
	prioridad = envios.value(envio,envios_ns.Prioridad)

	lotesCandidatos = []
	for l in lotes.subjects(predicate=lotes_ns.Ciudad,object=cp):
		if (lotes.value(subject=l,predicate=lotes_ns.Prioridad) == prioridad):
			lotesCandidatos += [l]


	lote = None

	if (len(lotesCandidatos) == 0):
		lote = crearLote(envio)
	else:
		lote = random.choice(lotesCandidatos)
		anadirEnvioLote(lote,envio)


def nuevoEnvio(graph):

	envio = graph.subjects(RDF.type,envios_ns.type).next()

	#Obtenemos solo la informacion que nos interesa
	graph = expandirGrafoRec(graph,envio)

	registrarEnvio(graph,envio)
	combinarLotes(envio)

	return create_confirm(AgenteEmpaquetador)

	#Buscar els lots de la ciutat x


def registerActions():
	global actions
	actions[agn.ReceptorNuevoEnvio] = nuevoEnvio

@app.route("/")
def main_page():
	"""
	El hola mundo de los servicios web
	:return:
	"""
	return "soy el agente empaquetador, hola!"



def start_server():
	cargarGrafos(centroLogistico)
	register_message(AgenteEmpaquetador,DirectorioAgentes,agenteEmpaquetador_ns.type)
	registerActions()
	app.run(host=host,port=port,debug=True)


if __name__ == "__main__":
	start_server()

