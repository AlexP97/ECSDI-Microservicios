# -*- coding: utf-8 -*-
"""
filename: DirectorioAgentes

Antes de ejecutar hay que añadir la raiz del proyecto a la variable PYTHONPATH

Agente que lleva un registro de otros agentes

Utiliza un registro simple que guarda en un grafo RDF

El registro no es persistente y se mantiene mientras el agente funciona

Las acciones que se pueden usar estan definidas en la ontología
directory-service-ontology.owl

"""

from __future__ import print_function
from multiprocessing import Process, Queue
import socket
import argparse

from flask import Flask, request, render_template
from rdflib import Graph, RDF, Namespace, RDFS, Literal
from rdflib.namespace import FOAF

from Util.OntoNamespaces import ACL, DSO
from Util.FlaskServer import shutdown_server
from Util.Agente import Agent
from Util.ACLMessages import build_message, get_message_properties
from Util.Namespaces import createAction
from Util.Namespaces import getNamespace,getAgentNamespace
from Util.General import * 
import random

# Logging



argumentos = getArguments(my_port=9000)
#Direcciones hardcodeadas (propia)
hostname = argumentos['host']
port = argumentos['port']

# Directory Service Graph
dsgraph = Graph()

#Grafo de estadisticas
stats = Graph()

# Vinculamos todos los espacios de nombre a utilizar
dsgraph.bind('acl', ACL)
dsgraph.bind('rdf', RDF)
dsgraph.bind('rdfs', RDFS)
dsgraph.bind('foaf', FOAF)
dsgraph.bind('dso', DSO)

#Pillamos el espacio de nombres de la referencia universal para nuestro agente
agn = getNamespace('AgenteDirectorio')


#Inicializamos el objeto agente con el nombre, la uri y las direcciones simples (que no utilizaremos)
DirectoryAgent = Agent('DirectoryAgent',
					   agn['Generic'],
					   'http://%s:%d/comm' % (hostname, port),
					   'http://%s:%d/Stop' % (hostname, port))

#Cambiamos la ruta del flask 
app = Flask(__name__,template_folder="DirectorioAgentes/templates")
mss_cnt = 0

cola1 = Queue()  # Cola de comunicacion entre procesos


@app.route("/comm")
def register():
	"""
	Entry point del agente que recibe los mensajes de registro
	La respuesta es enviada al retornar la funcion,
	no hay necesidad de enviar el mensaje explicitamente

	Asumimos una version simplificada del protocolo FIPA-request
	en la que no enviamos el mesaje Agree cuando vamos a responder

	"""

	def process_register():
		# Si la hay extraemos el nombre del agente (FOAF.Name), el URI del agente
		# su direccion y su tipo

		#logger.info('Peticion de registro')

		agn_add = gm.value(subject=content, predicate=DSO.Address)
		agn_name = gm.value(subject=content, predicate=FOAF.Name)
		agn_uri = gm.value(subject=content, predicate=DSO.Uri)
		agn_type = gm.value(subject=content, predicate=DSO.AgentType)

		# Añadimos la informacion en el grafo de registro vinculandola a la URI
		# del agente y registrandola como tipo FOAF.Agent
		dsgraph.add((agn_uri, RDF.type, FOAF.Agent))
		dsgraph.add((agn_uri, FOAF.name, agn_name))
		dsgraph.add((agn_uri, DSO.Address, agn_add))
		dsgraph.add((agn_uri, DSO.AgentType, agn_type))

		print("registro finalizado con exito")
		# Generamos un mensaje de respuesta
		return build_message(Graph(),
			ACL.confirm,
			sender=DirectoryAgent.uri,
			receiver=agn_uri,
			msgcnt=mss_cnt)

	def process_search():
		# Asumimos que hay una accion de busqueda que puede tener
		# diferentes parametros en funcion de si se busca un tipo de agente
		# o un agente concreto por URI o nombre
		# Podriamos resolver esto tambien con un query-ref y enviar un objeto de
		# registro con variables y constantes

		# Solo consideramos cuando Search indica el tipo de agente
		# Buscamos una coincidencia exacta
		# Retornamos el primero de la lista de posibilidades

		#logger.info('Peticion de busqueda')

		agn_type = gm.value(subject=content, predicate=DSO.AgentType)
		rsearch = dsgraph.triples((None, DSO.AgentType, agn_type))
		# Es mas simple evitar el hecho de que no hayan agentes en rsearch con la
		# captura de excepciones. el rsearch.next()[0] lanzara StopIteration si no hay elementos
		candidatos = list(rsearch)
		if len(candidatos) > 0: 

			agn_uri = random.choice(candidatos)[0]
			register_stat(agn_uri,agn_type)
			#agn_uri = rsearch.next()[0]
			agn_add = dsgraph.value(subject=agn_uri, predicate=DSO.Address)
			gr = Graph()
			gr.bind('dso', DSO)
			rsp_obj = createAction(DirectoryAgent,'search-response')
			#Anadimos las direcciones y el uri del agente que se buscaba
			gr.add((rsp_obj, DSO.Address, agn_add))
			gr.add((rsp_obj, DSO.Uri, agn_uri))
			return build_message(gr,
								 ACL.inform,
								 sender=DirectoryAgent.uri,
								 msgcnt=mss_cnt,
								 receiver=agn_uri,
								 content=rsp_obj)
		else:
			# Si no encontramos nada retornamos un inform sin contenido
			return build_message(Graph(),
				ACL.failure,
				sender=DirectoryAgent.uri,
				msgcnt=mss_cnt)
	def process_specificSearch():
		# Asumimos que hay una accion de busqueda que puede tener
		# diferentes parametros en funcion de si se busca un tipo de agente
		# o un agente concreto por URI o nombre
		# Podriamos resolver esto tambien con un query-ref y enviar un objeto de
		# registro con variables y constantes

		# Solo consideramos cuando Search indica el tipo de agente y la uri del agente
		# Buscamos una coincidencia exacta
		# Retornamos el primero de la lista de posibilidades

		#logger.info('Peticion de busqueda especifica')

		agn_type = gm.value(subject=content, predicate=DSO.AgentType)
		agn_uri = gm.value(subject=content,predicate=DSO.AgentUri)

		rsearch = dsgraph.triples((agn_uri, DSO.AgentType, agn_type))

		try:
			agn_uri = rsearch.next()[0]
			agn_add = dsgraph.value(subject=agn_uri, predicate=DSO.Address)
			gr = Graph()
			gr.bind('dso', DSO)
			rsp_obj = createAction(DirectoryAgent,'search-response')
			gr.add((rsp_obj, DSO.Address, agn_add))
			gr.add((rsp_obj, DSO.Uri, agn_uri))
			return build_message(gr,
								 ACL.inform,
								 sender=DirectoryAgent.uri,
								 msgcnt=mss_cnt,
								 receiver=agn_uri,
								 content=rsp_obj)
		except StopIteration:
			# Si no encontramos nada retornamos un inform sin contenido
			return build_message(Graph(),
				ACL.failure,
				sender=DirectoryAgent.uri,
				msgcnt=mss_cnt)

	def process_globalSearch():
		# Asumimos que hay una accion de busqueda que puede tener
		# diferentes parametros en funcion de si se busca un tipo de agente
		# o un agente concreto por URI o nombre
		# Podriamos resolver esto tambien con un query-ref y enviar un objeto de
		# registro con variables y constantes

		# Esta funcion busca todos los agentes de cierto tipo
		# Retornamos todos los agentes que estaban registrados en nuestro grafo

		#logger.info('Peticion de busqueda global')

		# Parseamos la peticion del tipo y buscamos en el grafo
		agn_type = gm.value(subject=content, predicate=DSO.AgentType)
		res_agents = dsgraph.subjects(predicate=DSO.AgentType, object=agn_type)

		gr = Graph()
		gr.bind('dso',DSO)

		# Aunque no haya agentes vamos a generar una respuesta afirmativa
		for agente in res_agents:

			# Generamos los direccion y el uri del agente para meterlos luego en el grafo
			uri = agente
			address = dsgraph.objects(subject=agente,predicate=DSO.Address).next()

			gr.add((uri,DSO.Address,address))
			# Para buscar todos los agentes utilizaremos el predicado DSO.Type desde el otro agente (Directorio.py)
			gr.add((uri,DSO.Type,DSO.Agent))

		return build_message(
			gr,
			ACL.inform,
			sender=DirectoryAgent.uri,
			msgcnt=mss_cnt,
		)

	global dsgraph
	global mss_cnt
	# Extraemos el mensaje y creamos un grafo con él
	message = request.args['content']
	gm = Graph()
	gm.parse(data=message)

	msgdic = get_message_properties(gm)

	# Comprobamos que sea un mensaje FIPA ACL
	if not msgdic:
		# Si no es, respondemos que no hemos entendido el mensaje
		gr = build_message(Graph(),
			ACL['not-understood'],
			sender=DirectoryAgent.uri,
			msgcnt=mss_cnt)
	else:
		# Obtenemos la performativa
		if msgdic['performative'] != ACL.request:
			# Si no es un request, respondemos que no hemos entendido el mensaje
			gr = build_message(Graph(),
				ACL['not-understood'],
				sender=DirectoryAgent.uri,
				msgcnt=mss_cnt)
		else:
			# Extraemos el objeto del contenido que ha de ser una accion de la ontologia
			# de registro
			content = msgdic['content']
			# Averiguamos el tipo de la accion
			accion = gm.value(subject=content, predicate=RDF.type)

			# Accion de registro
			if accion == DSO.Register:
				gr = process_register()
			# Accion de busqueda
			elif accion == DSO.Search:
				gr = process_search()
			# Accion de busqueda especifica
			elif accion == DSO.SearchSpecific:
				gr = process_specificSearch()
			# Accion de busqueda global
			elif accion == DSO.SearchGlobal:
				gr = process_globalSearch()
			# No habia ninguna accion en el mensaje
			else:
				gr = build_message(Graph(),
						ACL['not-understood'],
						sender=DirectoryAgent.uri,
						msgcnt=mss_cnt)
	mss_cnt += 1
	return gr.serialize(format='xml')

@app.route('/')
def main():
	return render_template('main.html')

@app.route('/Info')
def info():
	"""
	Entrada que da informacion sobre el agente a traves de una pagina web
	"""
	global dsgraph
	global mss_cnt

	return render_template('info.html', nmess=mss_cnt, graph=dsgraph.serialize(format='turtle'))

@app.route('/InfoStats')
def infoStats():
	return render_template('info.html', nmess=mss_cnt, graph=stats.serialize(format='turtle'))

def register_stat(agn_uri,agn_type):
	val = stats.value(agn_uri,DSO.nRequests) 
	if val is None:
		stats.add((agn_uri,RDF.type,DSO.Agent))
		stats.add((agn_uri,DSO.agentType,agn_type))
		stats.add((agn_uri,DSO.nRequests,Literal(1)))
	else:
		stats.set((agn_uri,DSO.nRequests,Literal(int(val) + 1)))

@app.route('/verStats')
def verStats():
	list = []
	for a in stats.subjects(predicate=RDF.type,object=DSO.Agent):
		dict ={}
		dict['URI'] = a
		dict['Type'] = stats.value(a,DSO.agentType)
		dict['Peticiones'] = stats.value(a,DSO.nRequests)
		list += [dict]

	return render_template('stats.html',list=list)

@app.route("/Stop")
def stop():
	"""
	Entrada que para el agente
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


def agentbehavior1(cola):
	"""
	Behaviour que simplemente espera mensajes de una cola y los imprime
	hasta que llega un 0 a la cola
	"""
	fin = False
	while not fin:
		while cola.empty():
			pass
		v = cola.get()
		if v == 0:
			print(v)
			return 0
		else:
			print(v)


if __name__ == '__main__':
	# Ponemos en marcha el servidor Flask
	app.run(host=hostname, port=port, debug=True)
	#logger.info('The End')
