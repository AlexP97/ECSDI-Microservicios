"""
.. module:: Example1

Example1
******

:Description: Example1

Ejemplos de RDFLIB

"""

from __future__ import print_function
from rdflib.namespace import RDF, RDFS, Namespace, FOAF, OWL
from rdflib import Graph, BNode, Literal
from pprint import pformat
__author__ = 'bejar'

g = Graph()

n = Namespace('http://tienda.org#')

producto = n.producto
predicado = n.precio 
v = Literal(22.5)

g.add((producto,predicado,v))

d = g.serialize('a.rdf',format="turtle")

for a, b, c in g:
    print(a, b, c)

for a, b in g[producto]:
    print(a, b)

t = g.triples((None, n.precio, Literal(22)))

for a in t:
    print(a)

print ("Grafo serializado")
print (d)