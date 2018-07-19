# -*- coding: utf-8 -*-
"""
filename: ACLMessages
Utilidades para tratar los mensajes FIPA ACL
Created on 08/02/2014
@author: javier
"""
__author__ = 'javier'

from rdflib import Graph
import requests
from rdflib.namespace import RDF

from Util.OntoNamespaces import ACL,DSO
from rdflib.namespace import FOAF, RDF



def build_message(gmess, perf, sender=None, receiver=None,  content=None, msgcnt= 0):
	"""
	Construye un mensaje como una performativa FIPA acl
	Asume que en el grafo que se recibe esta ya el contenido y esta ligado al
	URI en el parametro contenido
	:param gmess: grafo RDF sobre el que se deja el mensaje
	:param perf: performativa del mensaje
	:param sender: URI del sender
	:param receiver: URI del receiver
	:param content: URI que liga el contenido del mensaje
	:param msgcnt: numero de mensaje
	:return:
	"""
	# Añade los elementos del speech act al grafo del mensaje
	mssid = 'message-'+str(sender.__hash__()) + '-{:{fill}4d}'.format(msgcnt, fill='0')
	ms = ACL[mssid]
	gmess.bind('acl', ACL)
	gmess.add((ms, RDF.type, ACL.FipaAclMessage))
	gmess.add((ms, ACL.performative, perf))
	gmess.add((ms, ACL.sender, sender))

	if receiver is not None:
		gmess.add((ms, ACL.receiver, receiver))
	if content is not None:
		gmess.add((ms, ACL.content, content))  
	
	return gmess


def send_message(gmess, address):
	"""
	Envia un mensaje usando un request y retorna la respuesta como
	un grafo RDF
	"""
	msg = gmess.serialize(format='xml')
	#print "DEBUG: gmess after serializing to xml:\n"
	#print msg
	r = requests.get(address, params={'content': msg})

	#####
	print (r.status_code)
	#print r.text + '\n\n'
	# Procesa la respuesta y la retorna como resultado como grafo
	gr = Graph()
	#gr.add((ACL.status, ACL.status_code, Literal(r.status_code)))
	gr.parse(data=r.text)

	return gr


def get_message_properties(msg):
	"""
	Extrae las propiedades de un mensaje ACL como un diccionario.
	Del contenido solo saca el primer objeto al que apunta la propiedad
	Los elementos que no estan, no aparecen en el diccionario
	"""
	props = {'performative': ACL.performative, 'sender': ACL.sender,
			 'receiver': ACL.receiver, 'ontology': ACL.ontology,
			 'conversation-id': ACL['conversation-id'],
			 'in-reply-to': ACL['in-reply-to'], 'content': ACL.content}
	msgdic = {} # Diccionario donde se guardan los elementos del mensaje

	# Extraemos la parte del FipaAclMessage del mensaje
	valid = msg.value(predicate=RDF.type, object=ACL.FipaAclMessage)

	# Extraemos las propiedades del mensaje
	if valid is not None:
		for key in props:
			val = msg.value(subject=valid, predicate=props[key])
			if val is not None:
				msgdic[key] = val
	return msgdic

def create_confirm(agentSender = None,agentReciever = None):
	s_uri = None
	r_uri = None
	if agentReciever is not None:
		r_uri = agentReciever.uri
	if agentSender is not None:
		s_uri = agentSender.uri

	return build_message(
		Graph(),
		ACL.confirm,
		sender=s_uri,
		receiver=r_uri
		)

def create_notUnderstood(agentSender,agentReciever):
	if agentReciever is None:
		return build_message(Graph(),ACL['not-understood'],sender=agentSender.uri)
		
	return build_message(
		Graph(),
		ACL['not-understood'],
		sender=agentSender.uri,
		reciever=agentReciever.uri
		)


'''
parsea un mensaje y retorna un diccionario con las propiedades de este.
Esta funcion no es necesaria si se supone que todos los mensajes seran correctos
'''
def parse_message(graph,performative=None,actions=None):
	# Extraemos el mensaje y creamos un grafo con él
	msgdic = get_message_properties(graph)

	if not msgdic: 
		return False
	if performative != None and msgdic['performative'] != performative: 
		return False

	# Extraemos la accion del mensaje
	content = msgdic['content']
	# Averiguamos el tipo de la accion
	accion = graph.value(subject=content, predicate=RDF.type)

	# Si la accion no es la especificada en la cabecera significa que el mensaje es erroneo
	if actions != None and not accion in actions:
		return False

	#Diccionario de retorno. 
	ret = {
		'msgdic':msgdic,
		'accion':accion
	}
	return ret