from __future__ import print_function
from multiprocessing import Process

import socket
import os.path
#Clase agente
from Util.Agente import Agent
#Renders del flask
from flask import Flask, request, render_template,redirect
from time import sleep
#Funciones para recuperar las direcciones de los agentes
from Util.GestorDirecciones import formatDir
from Util.ACLMessages import build_message, get_message_properties, send_message
from Util.OntoNamespaces import ACL, DSO
from Util.Directorio import *
#Diccionario con los espacios de nombres de la tienda
from Util.Namespaces import *
from Util.GraphUtil import *
#Utilidades de RDF
from rdflib import Graph, Namespace, Literal,BNode
from rdflib.namespace import FOAF, RDF
from rdflib.collection import Collection
from Util.GraphUtil import *
from Util.ModelParser import *
from Util.General import *
import datetime
import random
import math
