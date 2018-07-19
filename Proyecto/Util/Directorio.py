'''
Libreria de alto nivel para los mensajes.
Tenemos 3 maneras de enviar mensajes:
	1: send_message_any: Envia a 1 agente del tipo Type
	2: send_message_uri: Envia a 1 agente del tipo Type y con la Uri especificada 
	(Supongo que suprimiremos la restriccion de type aqui, depende de los namespaces)
	3: send_message_all: Envia un mensaje a todos los agentes del tipo Type. Devuelve una lista de respuestas

Las otras 3 funciones no son en principio necesarias para nada (register_...)
Solo sirven para desacoplar funcionalidades.

'''

from __future__ import print_function
from multiprocessing import Process, Queue
import socket
import argparse

from flask import Flask, request
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import FOAF, RDF

from Util.OntoNamespaces import ACL, DSO
from Util.ACLMessages import *
from Util.Agente import Agent
from Util.Logging import config_logger
from Util.Namespaces import createAction

def register_message(agentSender,directoryAgent,agentType):
	"""
	Envia un mensaje de registro al servicio de registro
	usando una performativa Request y una accion Register del
	servicio de directorio

	:param gmess:
	:return:
	"""
	gmess = Graph()
	# Construimos el mensaje de registro. Anadimos las ontologias FOAF y DSO que aunque no son 
	# necesarias para nuestro contexto, se pueden utilizar.
	gmess.bind('foaf', FOAF)
	gmess.bind('dso', DSO)
	#el reg_obj sirve como nodo sujeto de todos los atributos de la comunicacion
	reg_obj = createAction(agentSender,'register')
	#Anadimos los atributos de la comunicacion. La accion es de registro por lo que mandamos nuestros datos
	gmess.add((reg_obj, RDF.type, DSO.Register))
	gmess.add((reg_obj, DSO.Uri, agentSender.uri))
	gmess.add((reg_obj, FOAF.Name, Literal(agentSender.name)))
	gmess.add((reg_obj, DSO.Address, Literal(agentSender.address)))
	gmess.add((reg_obj, DSO.AgentType, agentType))

	# Lo metemos en un envoltorio FIPA-ACL y lo enviamos al directorio
	gr = send_message(
		build_message(gmess, perf=ACL.request,
					  sender=agentSender.uri,
					  receiver=directoryAgent.uri,
					  content=reg_obj),
		directoryAgent.address)
	return gr



def directory_search_message(agentSender,directoryAgent,type):
	"""
	Busca en el servicio de registro mandando un
	mensaje de request con una accion Seach del servicio de directorio
	"""
	gmess = Graph()

	gmess.bind('foaf', FOAF)
	gmess.bind('dso', DSO)
	#Nodo padre de la comunicacion
	reg_obj = createAction(agentSender,'search')
	#Especificamos que queremos hacer una busqueda normal y anadimos el tipo de agente
	gmess.add((reg_obj, RDF.type, DSO.Search))
	gmess.add((reg_obj, DSO.AgentType, type))

	#Enviamos el mensaje en FIPA-ACL
	msg = build_message(gmess, perf=ACL.request,
						sender=agentSender.uri,
						receiver=directoryAgent.uri,
						content=reg_obj)
	gr = send_message(msg, directoryAgent.address)
	return gr

def directory_search_specific(agentSender,directoryAgent,type,uri):
	"""
	Busca un agente del tipo type y con la uri especificada en el servicio de directorio
	"""
	gmess = Graph()
	gmess.bind('foaf', FOAF)
	gmess.bind('dso', DSO)
	reg_obj = createAction(agentSender,'search-specific')
	gmess.add((reg_obj, RDF.type, DSO.SearchSpecific))
	gmess.add((reg_obj, DSO.AgentType, type))
	#La unica diferencia con el search message es esta nueva relacion,
	#que especifica la uri del agente a buscar
	gmess.add((reg_obj, DSO.AgentUri, uri))

	msg = build_message(gmess, perf=ACL.request,
						sender=agentSender.uri,
						receiver=directoryAgent.uri,
						content=reg_obj)
	gr = send_message(msg, directoryAgent.address)
	return gr

def directory_search_global(agentSender,directoryAgent,type):
	"""
	Busca todos los agentes del tipo type
	"""
	gmess = Graph()
	gmess.bind('foaf', FOAF)
	gmess.bind('dso', DSO)
	reg_obj = createAction(agentSender,'search-global')
	#La accion es diferente. El servicio de directorio ya se encargara de procesar esta informacion
	gmess.add((reg_obj, RDF.type, DSO.SearchGlobal))
	gmess.add((reg_obj, DSO.AgentType, type))

	msg = build_message(gmess, perf=ACL.request,
						sender=agentSender.uri,
						receiver=directoryAgent.uri,
						content=reg_obj)
	gr = send_message(msg, directoryAgent.address)
	return gr

def send_message_any(msg,agentSender,directoryAgent,type):
	''' 
	msg: grafo 
	agentSender / directoryAgent: objetos agente que representan el enviador y el receptor
	type: tipo de agente a buscar 
	devuelve: grafo del mensaje de retorno del agente (despues de contactar con el)
	'''
	#Buscamos un agente disponible
	res = directory_search_message(agentSender,directoryAgent,type)
	#Parseador para filtrar mensajes de error y similares (lanzara una excepcion si eso ocurre)
	parse = parse_message(res,performative=ACL.inform)
	if not parse:
		raise Exception('Agente no encontrado')
   
   	#Pillamos el sujeto padre de la comunicacion de vuelta ya que la respuesta solo tiene 1 agente
	node = parse['msgdic']['content'] 
	#Solo nos interesa la direccion. TODO ampliar tambien a URI?  
	address = res.objects(node,DSO.Address).next()
	return send_message(msg,address)

def send_message_uri(msg,agentSender,directoryAgent,type,uri):
	''' 
	msg: grafo 
	agentSender / directoryAgent: objetos agente que representan el enviador y el receptor
	type: tipo de agente a buscar 
	uri: direccion del agente a buscar
	devuelve: grafo del mensaje de retorno del agente (despues de contactar con el)
	'''
	res = directory_search_specific(agentSender,directoryAgent,type,uri)
	parse = parse_message(res,performative=ACL.inform)
	if not parse:
		raise Exception('Agente no encontrado')

	node = parse['msgdic']['content']
	address = res.objects(node,DSO.Address).next()
	return send_message(msg,address)

def send_message_all(msg,agentSender,directoryAgent,type):
	''' 
	msg: grafo 
	agentSender / directoryAgent: objetos agente que representan el enviador y el receptor
	type: tipo de agente a buscar 
	devuelve: grafo del mensaje de retorno del agente (despues de contactar con el)
	'''
	res = directory_search_global(agentSender,directoryAgent,type)
	agentes = res.subjects(predicate=DSO.Type,object=DSO.Agent)
	responses = []
	#Enviamos un mensaje para cada agente (TODO se puede enfocar de forma concurrente) y esperamos las respuestas
	for agente in agentes:
		address = res.objects(subject=agente,predicate=DSO.Address).next()
		responses += [
			{
			"uri":agente,
			"msg":send_message(msg,address)
			}
		]
	return responses


def send_message_set(msg,agentSender,directoryAgent,type,uris):
	''' 
	msg: grafo 
	agentSender / directoryAgent: objetos agente que representan el enviador y el receptor
	type: tipo de agente a buscar 
	devuelve: grafo del mensaje de retorno del agente (despues de contactar con el)
	'''
	res = directory_search_global(agentSender,directoryAgent,type)
	agentes = res.subjects(predicate=DSO.Type,object=DSO.Agent)
	responses = []
	#Enviamos un mensaje para cada agente que este dentro de la subseleccion
	#(TODO se puede enfocar de forma concurrente) y esperamos las respuestas
	#uris = [str(s) for s in uris]
	for agente in agentes:
		if agente in uris:
			address = res.objects(subject=agente,predicate=DSO.Address).next()
			responses += [
				{
				"uri":agente,
				"msg":send_message(msg,address)
				}
			]
	return responses


def get_all_uris(agentSender,directoryAgent,type):
	res = directory_search_global(agentSender,directoryAgent,type)
	agentes = res.subjects(predicate=DSO.Type,object=DSO.Agent)
	return list(agentes)