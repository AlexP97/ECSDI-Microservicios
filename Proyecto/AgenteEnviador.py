from imports import *

app = Flask(__name__,template_folder="AgenteEnviador/templates")

#Direcciones hardcodeadas (propia)

argumentos = getArguments(my_port=8005,name="enviador")
#Direcciones hardcodeadas (propia)
host = argumentos['host']
port = argumentos['port']

#Nombre del vendedor externo. Servira para generar una URI de recurso
#Aun asi es probable que solo utilitzemos 1 vendedor
nombre = argumentos['name']

directorio_host = argumentos['dir_host']
directorio_port = argumentos['dir_port']

addr = argumentos['addr']

enviador = getNamespace('AgenteEnviador')
transportista_ns = getNamespace('AgenteTransportista')
productos = getNamespace('Productos')
pedidos = getNamespace('Pedidos')
lotes_ns = getNamespace('Lotes')
envios_ns = getNamespace('Envios')
vendedor = getNamespace('AgenteVendedorExterno')
ofertas_ns = getNamespace('Ofertas')

agn = getAgentNamespace()

g = Graph()

envios = Graph()

#Objetos agente, no son necesarios en toda regla pero sirven para agilizar comunicaciones
AgenteEnviador = Agent('AgenteEnviador',enviador[nombre],formatDir(addr,port) + '/comm',None)
DirectorioAgentes = Agent('DirectorioAgentes',agn.Directory,formatDir(directorio_host,directorio_port) + '/comm',None)
#Cargar el grafo de datos
graphFile = 'Datos/Lotes/' + nombre + '.turtle'
enviosFile = 'Datos/Envios/' + nombre + '.turtle'
#Acciones. Este diccionario sera cargado con todos los procedimientos que hay que llamar dinamicamente
# cuando llega un mensaje
actions = {}

#Carga el grafo rdf del fichero graphFile
def cargarGrafo():
	global g
	g = Graph()
	if os.path.isfile(graphFile):
		g.parse(graphFile,format="turtle")

def cargarGrafos():
	global g,envios
	g = Graph()
	envios = Graph()
	if os.path.isfile(graphFile):
		g.parse(graphFile,format="turtle")
	if os.path.isfile(enviosFile):
		envios.parse(enviosFile,format="turtle")

def guardarGrafos():
	global g,envios
	g.serialize(graphFile,format='turtle')
	envios.serialize(enviosFile,format='turtle')

@app.route("/comm")
def comunicacion():
	# Extraemos el mensaje y creamos un grafo con el
	cargarGrafos()
	g.serialize('test.turtle',format='turtle')
	message = request.args['content']
	gm = Graph()
	gm.parse(data=message)

	msgdic = get_message_properties(gm)
	gr = None
	# Comprobamos que sea un mensaje FIPA ACL y que la performativa sea correcta
	if not msgdic:
		# Si no es, respondemos que no hemos entendido el mensaje
		gr = create_notUnderstood(AgenteEnviador,None)
	else:
		content = msgdic['content']
		# Averiguamos el tipo de la accion
		accion = gm.value(subject=content, predicate=RDF.type)

		#Llamada dinamica a la accion correspondiente
		if accion in actions:
			gr = actions[accion](gm)
		else:
			gr = create_notUnderstood(AgenteEnviador,None)

	return gr.serialize(format='xml')

@app.route("/verLotes")
def verLotes():
	cargarGrafos()
	g.serialize('test.turtle',format='turtle')
	lotes = g.subjects(predicate=RDF.type,object=lotes_ns.type)
	list = []
	for l in lotes:
		d = lote_a_dict(g,l)
		#Preveimos el bug de enviar un lote ya enviado
		list += [d]
	return render_template('listaLotes.html',list=list)

def getPesoLote(id):
	peso = int(g.value(lotes_ns[id],lotes_ns.Peso))
	return peso


def calcularImporteTotalEnvio(envio,lote,importeEnvioLote):
	importeBase = float(envios.value(envio,envios_ns.Importetotal))
	pesoEnvio = envios.value(envio,envios_ns.Peso)
	pesoLote = g.value(lote,lotes_ns.Peso)
	importeEnvio = float(importeEnvioLote) * float(str(pesoLote)) / float(str(pesoEnvio))
	return math.ceil(importeEnvio)

def cobrarEnvio(envio,importe):
	gcom = Graph()

	obj = createAction(AgenteEnviador,'cobrarPedido')

	uri_user = envios.value(envio,envios_ns.Hechopor)

	gcom.add((obj, RDF.type, agn.MonetarioPedirPagoPedido))
	gcom.add((obj, pagos_ns.SeHaceA, uri_user))
	gcom.add((obj, pagos_ns.Importe,Literal(importe)))
	# Lo metemos en un envoltorio FIPA-ACL y lo enviamos
	msg = build_message(gcom,
		perf=ACL.inform,
		sender=AgenteEnviador.uri,
		content=obj)

	# Enviamos el mensaje a cualquier agente monetario
	send_message_any(msg,AgenteEnviador,DirectorioAgentes,agenteMonetario_ns.type)

def obtenerEnviosDeLote(lote):
	ret = []
	node = g.value(subject=lote,predicate=lotes_ns.TieneEnvios)
	c = Collection(g,node)
	for pedido in c:
		ret+=[pedido]
	return ret



def enviarConfirmacionTienda(envio,importe,transportista):
	gcom = Graph()

	obj = createAction(AgenteEnviador,'confirmarCompra')

	gcom.add((obj, RDF.type, agn.EnviadorConfirmarEnvio))
	gcom.add((obj, pedidos_ns.ImporteEnvio,Literal(importe)))
	gcom.add((obj, pedidos_ns.LoTransporta,transportista))
	gcom.add((obj, pedidos_ns.CentroResponsable,centros_ns[nombre]))
	#Ponemos el envio que hemos realizado
	gcom += expandirGrafoRec(envios,envio)
	# Lo metemos en un envoltorio FIPA-ACL y lo enviamos
	msg = build_message(gcom,
		perf=ACL.inform,
		sender=AgenteEnviador.uri,
		content=obj)

	# Enviamos el mensaje a cualquier agente monetario
	send_message_any(msg,AgenteEnviador,DirectorioAgentes,agenteReceptor_ns.type)

def registrarLoteEnviado(lote,envios_realizados):
	g.set((lote,lotes_ns.Estadodellote,Literal('Enviado')))
	for e in envios_realizados:
		envios.set((e,envios_ns.EstadoEnvio,Literal('Enviado')))

	guardarGrafos()


def aceptarOferta(transportista,precio,lote):
	#Sumar el importe proporcional a los envios que estaban dentro de lote
	envios = obtenerEnviosDeLote(lote)
	#Hacemos esto antes porque sino no se envia el estado correctamente al usuario
	registrarLoteEnviado(lote,envios)
	for e in envios:
		importe = calcularImporteTotalEnvio(e,lote,precio)
		cobrarEnvio(e,importe)
		enviarConfirmacionTienda(e,importe,transportista)
		
	


@app.route("/pedirOferta")
def pedirOferta():
	id = request.args['id']
	obj = createAction(AgenteEnviador,'peticionOferta')
	gcom = Graph()

	gcom.add((obj,RDF.type,agn.EnviadorPeticionOferta))
	gcom.add((obj,ofertas_ns.Peso,Literal(getPesoLote(id))))

	msg = build_message(gcom,
		perf=ACL.inform,
		sender=AgenteEnviador.uri,
		content=obj)

	responses = send_message_all(msg,AgenteEnviador,DirectorioAgentes,transportista_ns.type)
	
	ofertas = {}

	for item in responses:
		graph = item['msg']
		uri = item['uri']
		precio = math.ceil(float(graph.value(subject=ofertas_ns['0'], predicate=ofertas_ns.Oferta)))
		ofertas[uri] = precio

	if len(ofertas) == 0: raise Exception('No hay ningun transportista disponible')

	ganador = min(ofertas, key=ofertas.get)

	aceptarOferta(ganador,ofertas[ganador],lotes_ns[id])
	#ofertaTransporte(graph_min, id)
	return redirect("/verLotes")


def registerActions():
	global actions
	#actions[agn.EnviadorOfertaTransporte] = ofertaTransporte

def guardarGrafo():
	g.serialize(graphFile,format="turtle")


@app.route("/")
def main_page():
	"""
	El hola mundo de los servicios web
	:return:
	"""
	return render_template('main.html')


def start_server():
	register_message(AgenteEnviador,DirectorioAgentes,enviador.type)
	registerActions()
	cargarGrafos()
	#createFakeLote()	# Borrar quan tot funcioni
	app.run(host=host,port=port,debug=True)

if __name__ == "__main__":
	start_server()
