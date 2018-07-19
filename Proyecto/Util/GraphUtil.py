''' Utilidades del objeto grafo de rdt '''
from rdflib import Graph

''' 
recorrido DFS del grafo a partir de un node en especifico. 
Util para encontrar todos los atributos de un cierto recurso en recursivo 
'''
def expandirGrafoRec(grafo,nodo):
	g = Graph()
	for (s,p,o) in grafo.triples((nodo,None,None)):
		g.add((s,p,o))
		g+= expandirGrafoRec(grafo,o)
	return g

def borrarNodoRec(grafo,nodo):
	toDelete = []
	for (s,p,o) in grafo.triples((nodo,None,None)):
		borrarNodoRec(grafo,o)
		toDelete += [s]

	for d in toDelete:
		grafo.remove((d,None,None))

	
''' recorre el grafo a partir del nodo y transforma toda su estructura de manera recursiva en un diccionario '''
def grafoADict(grafo,nodo):
	ret = {}
	i = 0
	for (s,p,o) in grafo.triples((nodo,None,None)):
		ret[str(p)] = grafoADict(grafo,o)
		i+=1
	if i == 0: 
		return str(nodo)
	else:
		return ret
