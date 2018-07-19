
from Namespaces import *
from rdflib import Graph, Namespace, Literal,BNode
from rdflib.namespace import FOAF, RDF
from rdflib.collection import Collection
from GraphUtil import *
import random

def add_localizacion_node(graph,node,predicate,dir,cp):
	loc = generate_localizacion(dir,cp)
	parent = loc.subjects(RDF.type,direcciones_ns.type).next()
	graph+=loc
	graph.add((node,predicate,parent))

def generate_localizacion(dir,cp):
	ret = Graph()
	dir = dir.replace(' ','_')
	localizacion = direcciones_ns[str(dir)+str(cp)]
	ret.add((localizacion,RDF.type,direcciones_ns.type))
	ret.add((localizacion,direcciones_ns.Direccion,Literal(dir)))
	ret.add((localizacion,direcciones_ns.Codigopostal,Literal(cp)))

	return ret

def pedido_a_dict(graph,pedido):
	''' devuelve un diccionario con todos los atributos de producto '''
	pedidos_ns = getNamespace('Pedidos')
	direcciones_ns = getNamespace('Direcciones')
	productos_ns = getNamespace('Productos')
	ret = {}
	ret['id'] = graph.value(pedido,pedidos_ns.Id)
	ret['user_id'] = graph.value(pedido,pedidos_ns.Hechopor)
	ret['date'] = graph.value(pedido,pedidos_ns.Fecharealizacion)
	ret['prioridad'] = graph.value(pedido,pedidos_ns.Prioridad)
	ret['responsable'] = graph.value(pedido,pedidos_ns.VendedorResponsable) or False

	loc = graph.value(pedido,pedidos_ns.Tienedirecciondeentrega)
	ret['direccion'] = graph.value(loc,direcciones_ns.Direccion)
	ret['cp'] = graph.value(loc,direcciones_ns.Codigopostal)

	prods = []
	container = graph.value(subject=pedido,predicate=pedidos_ns.Contiene)

	c = Collection(graph,container)

	for item in c:
		dict = {}
		dict['uri'] = graph.value(subject=item,predicate=productosPedido_ns.AsociadoAlProducto)
		dict['estado'] = graph.value(subject=item,predicate=productosPedido_ns.EstadoProductoEnPedido)
		dict['fechaEntrega'] = graph.value(subject=item,predicate=productosPedido_ns.FechaEnvio)
		prods += [dict]

	ret['productos'] = prods
	return ret

def dict_a_pedido(dict):

	ret = Graph()

	pedidos_ns = getNamespace('Pedidos')
	direcciones_ns = getNamespace('Direcciones')
	usuarios_ns = getNamespace('AgenteUsuario')
	vendedores_ns = getNamespace('AgenteVendedorExterno')

	id = dict['id']
	user_id = dict['user_id']
	fecha = dict['date']
	prioridad = dict['prioridad']
	direccion = dict['direccion']
	cp = dict['cp']
	direccion_id = direccion + cp


	#Nodo padre y su tipo
	ret.add((pedidos_ns[id],RDF.type,pedidos_ns.type))
	ret.add((pedidos_ns[id],pedidos_ns.id,Literal(id)))

	#Anadimos el nodo de la direccion con su tipo y todo
	add_localizacion_node(ret,pedidos_ns[id],pedidos_ns.Tienedirecciondeentrega,direccion,cp)

	ret.add((pedidos_ns[id],pedidos_ns.Fecharealizacion,Literal(fecha)))
	ret.add((pedidos_ns[id],pedidos_ns.Prioridad,Literal(prioridad)))
	ret.add((pedidos_ns[id],pedidos_ns.Hechopor,usuarios_ns[user_id]))

	return ret



def producto_a_dict(graph,producto):
	# Anadimos los atributos que queremos renderizar a la vista
	dic = {}
	productos_ns = getNamespace('Productos')
	centros_ns = getNamespace('Centros')
	dic['nom'] = graph.value(subject = producto,predicate = productos_ns.Nombre)
	dic['preu'] = graph.value(subject = producto,predicate = productos_ns.Importe)
	dic['id'] = graph.value(subject = producto,predicate = productos_ns.Id)
	dic['enVenta'] = graph.value(subject = producto,predicate = productos_ns.enVenta)

	container = graph.value(subject=producto,predicate=productos_ns.CentrosLogisticos)

	c = Collection(graph,container)
	centros = []
	for item in c:
		dict = {}
		dict['id'] = graph.value(subject=item,predicate=centros_ns.Id)
		centros += [dict]

	dic['centros'] = centros
	return dic


def centro_a_dict(graph,centro):
	dic = {}
	centros_ns = getNamespace('Centros')
	direcciones_ns = getNamespace('Direcciones')
	dic['id'] = graph.value(subject=centro,predicate=centros_ns.Id)

	loc = graph.value(centro,centros_ns.Ubicadoen)
	dic['direccion'] = graph.value(loc,direcciones_ns.Direccion)
	dic['cp'] = graph.value(loc,direcciones_ns.Codigopostal)

	return dic

def dict_a_centro(dict):
	g = Graph()
	centros_ns = getNamespace('Centros')
	direcciones_ns = getNamespace('Direcciones')

	id = dict['id']
	cp = dict['cp']
	dir = dict['direccion']

	centro = centros_ns[id]

	g.add((centro,centros_ns.Id,Literal(id)))
	g.add((centro,RDF.type,centros_ns.type))

	add_localizacion_node(g,centro,centros_ns.Ubicadoen,dir,cp)

	return g

def pedido_a_envio(graph,pedido,productos):
	'''
	devuelve el pedido transformado en un envio
	Graph tiene que contener toda la informacion del pedido + toda la informacion de los productos
	para cada producto del pedido (importe mas que nada)
	'''

	g = Graph()

	envios_ns = getNamespace('Envios')
	pedidos_ns = getNamespace('Pedidos')
	productos_ns = getNamespace('Productos')

	#Generamos un id aleatorio
	envio_id = str(random.getrandbits(64))

	#Anadimos el ID al envio
	g.add((envios_ns[envio_id],RDF.type,envios_ns.type))
	g.add((envios_ns[envio_id],envios_ns.Id,Literal(envio_id)))

	#Anadimos el usuario al envio
	user = graph.value(pedido,pedidos_ns.Hechopor)
	g.add((envios_ns[envio_id],envios_ns.Hechopor,user))

	#Anadimos la referencia al pedido original
	pedido_uri = pedido
	g.add((envios_ns[envio_id],envios_ns.Llevaacabo,pedido_uri))


	#fecha de realizacion
	fecha = graph.value(pedido,pedidos_ns.Fecharealizacion)
	g.add((envios_ns[envio_id],envios_ns.Fecharealizacion,fecha))


	#direccion de entrega
	loc = graph.value(pedido,pedidos_ns.Tienedirecciondeentrega)
	locGraph = expandirGrafoRec(graph,loc)

	#sumamos la localizacion al grafo que devolvemos
	g+=locGraph
	g.add((envios_ns[envio_id],envios_ns.Tienedirecciondeentrega,loc))

	#Anadimos el conjunto de productos al grafo de envio. Hay que crear un nodo no anonimo para la lista
	# o sino la libreria no funciona bien
	lista = envios_ns[envio_id + '-ListaProductos']
	g.add((envios_ns[envio_id],envios_ns.Contiene,lista))
	c = Collection(g,lista)

	#Anadimos las uris de los productos al envio y sumamos el importe total
	importe = 0
	for p in productos:
		c.append(p)
		importe += int(graph.value(p,productos_ns.Importe))


	#Anadimos el importe total
	g.add((envios_ns[envio_id],envios_ns.Importetotal,Literal(importe)))

	#Anadimos la prioridad del envio que es la misma que la prioridad de la entrega
	prioridad = graph.value(pedido,pedidos_ns.Prioridad)
	g.add((envios_ns[envio_id],envios_ns.Prioridad,prioridad))

	return g

# Lotes
def lote_a_dict(graph,lote):
	''' devuelve un diccionario con todos los atributos del lote '''
	lotes_ns = getNamespace('Lotes')
	direcciones_ns = getNamespace('Direcciones')
	envios_ns = getNamespace('Envios')
	ret = {}
	ret['Id'] = graph.value(lote,lotes_ns.Id)
	ret['Estadodellote'] = str(graph.value(lote,lotes_ns.Estadodellote))
	ret['Ciudad'] = graph.value(lote,lotes_ns.Ciudad)
	ret['Peso'] = graph.value(lote,lotes_ns.Peso)
	ret['Prioridad'] = graph.value(lote,lotes_ns.Prioridad)

	#loc = graph.value(lote,lotes_ns.Tienedirecciondeentrega)
	#ret['direccion'] = graph.value(loc,direcciones_ns.Direccion)
	#ret['cp'] = graph.value(loc,direcciones_ns.Codigopostal)

	envs = []
	container = graph.value(subject=lote,predicate=lotes_ns.TieneEnvios)

	c = Collection(graph,container)

	for item in c:
		envs += [item]

	ret['envios'] = envs
	return ret

def transaccion_a_dict(graph,tr):

	ret = {}

	ret['id'] = graph.value(subject=tr,predicate=transacciones_ns.Id)
	ret['origen'] = graph.value(subject=tr,predicate=transacciones_ns.Origen)
	ret['destinatario'] = graph.value(subject=tr,predicate=transacciones_ns.Destinatario)
	ret['formaOrigen'] = graph.value(subject=tr,predicate=transacciones_ns.FormaOrigen)
	ret['formaDestinatario'] = graph.value(subject=tr,predicate=transacciones_ns.FormaDestino)
	ret['importe'] = graph.value(subject=tr,predicate=transacciones_ns.Importe)
	
	return ret
