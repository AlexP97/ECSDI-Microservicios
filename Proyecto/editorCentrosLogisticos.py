# -*- coding: utf-8 -*-
from imports import * 


argumentos = getArguments(my_port=8020)
#Direcciones hardcodeadas (propia)
host = argumentos['host']
port = argumentos['port']

graphFile = 'Datos/centros.turtle'
#grafo de centros
g = Graph()

#Carga el grafo rdf del fichero graphFile
def cargarGrafo():
	g = Graph()
	if os.path.isfile(graphFile):
		g.parse(graphFile,format="turtle")
	return g

def cargarGrafoPesosCentro(centro):
	g = Graph()
	file = 'Datos/Pesos/' + centro + '.turtle'
	print(file)
	if os.path.isfile(file):
		g.parse(file,format="turtle")
	return g

def guardarGrafoPesosCentro(centro,grafo):
	file = 'Datos/Pesos/' + centro + '.turtle'
	grafo.serialize(file,format="turtle")

def guardarGrafo():
	g.serialize(graphFile,format="turtle")

#Cambiamos la ruta por defecto de los templates para que sea dentro de los ficheros del agente
app = Flask(__name__,template_folder="SharedTemplates")
#Espacios de nombres utilizados
#Espacio de los agentes en general

#cargamos el grafo
g = cargarGrafo()

centros_ns = getNamespace('Centros')

@app.route("/")
def main_page():

	centros = g.subjects(predicate=RDF.type,object=centros_ns.type)

	list = []
	for c in centros:
		print(c)
		list += [centro_a_dict(expandirGrafoRec(g,c),c)]

	return render_template('centros_main.html',list=list)


@app.route("/crearCentro")
def crearCentro():
	return render_template('centros_new.html')

@app.route("/borrarCentro")
def borrarCentro():

	global g
	
	id = request.args['id']

	centro = expandirGrafoRec(g,centros_ns[id])

	g-=centro

	guardarGrafo()

	return redirect("/")

@app.route("/nuevoCentro")
def nuevoCentro():
	global g
	direcciones_ns = getNamespace('Direcciones')

	centro = dict_a_centro(request.args)

	g+=centro
	guardarGrafo()

	return redirect("/")

@app.route("/centros/<id>/productos")
def verListaProductosCentro(id):
	g = cargarGrafoPesosCentro(id)

	centros_ns = getNamespace('Centros')
	productos_ns = getNamespace('Productos')
	centro = centros_ns[id]
	node =  g.value(subject=centro,predicate=centros_ns.Contiene) or centros_ns[id + '-listaProductos']

	#Afegim el node pare de la coleccio de productes
	g.add((centro,centros_ns.Contiene,node))

	c = Collection(g,node)
	list = []
	for prod in c:
		dict = {}
		dict['id'] = g.value(prod,productos_ns.Id)
		dict['peso'] = g.value(prod,productos_ns.Peso)
		list += [dict]
	return render_template("centros_listaProductos.html",list=list,id=id)

@app.route("/centros/<idCentro>/productos/<idProducto>/editar")
def editarProductoCentro(idCentro,idProducto):
	pass

@app.route("/centros/<idCentro>/productos/<idProducto>/borrar")
def borrarProductoCentro(idCentro,idProducto):
	productos_ns = getNamespace('Productos')
	centros_ns = getNamespace('Centros')

	centro = centros_ns[idCentro]
	g = cargarGrafoPesosCentro(idCentro)

	#nodo padre de la lista
	node =  g.value(subject=centro,predicate=centros_ns.Contiene) or centros_ns[idCentro + '-listaProductos']

	#Anadimos el nodo padre de la coleccion de productos en todos los casos
	g.add((centro,centros_ns.Contiene,node))

	c = Collection(g,node)

	toDelete = productos_ns[idProducto]

	del c[c.index(toDelete)]

	g.remove((toDelete,None,None))

	guardarGrafoPesosCentro(idCentro,g)

	return redirect("/centros/" + idCentro + "/productos")

@app.route("/centros/<idCentro>/crearProducto")
def crearProductoCentro(idCentro):
	return render_template("centros_crearProducto.html",id=idCentro)

@app.route("/centros/<idCentro>/submitProducto")
def submitProductoCentro(idCentro):
	productos_ns = getNamespace('Productos')
	centros_ns = getNamespace('Centros')

	g = cargarGrafoPesosCentro(idCentro)

	centro = centros_ns[idCentro]

	#nodo padre de la lista
	node =  g.value(subject=centro,predicate=centros_ns.Contiene) or centros_ns[idCentro + '-listaProductos']

	#Anadimos el nodo padre de la coleccion de productos en todos los casos
	g.add((centro,centros_ns.Contiene,node))

	c = Collection(g,node)

	#Creamos el producto con los datos
	idProducto = request.args['id']
	peso = request.args['peso']

	prod = productos_ns[idProducto]

	g.add((prod,RDF.type,productos_ns.type))
	g.add((prod,productos_ns.Id,Literal(idProducto)))
	g.add((prod,productos_ns.Peso,Literal(peso)))

	c.append(prod)

	guardarGrafoPesosCentro(idCentro,g)

	return redirect("/centros/" + idCentro + "/productos")

def tidyup():
	#Instrucciones de parada
	guardarGrafo()

def start_server():
	app.run(host=host,port=port,debug=True)


if __name__ == "__main__":
	start_server()

