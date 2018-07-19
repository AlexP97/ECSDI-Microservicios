# -*- coding: utf-8 -*-
from imports import * 


argumentos = getArguments(my_port=8021)
#Direcciones hardcodeadas (propia)
host = argumentos['host']
port = argumentos['port']

graphFile = 'Datos/personas.turtle'
#grafo de centros
g = Graph()

#Carga el grafo rdf del fichero graphFile
def cargarGrafo():
	g = Graph()
	if os.path.isfile(graphFile):
		g.parse(graphFile,format="turtle")
	return g

def guardarGrafo():
	g.serialize(graphFile,format="turtle")

#Cambiamos la ruta por defecto de los templates para que sea dentro de los ficheros del agente
app = Flask(__name__,template_folder="SharedTemplates")
#Espacios de nombres utilizados
#Espacio de los agentes en general

#cargamos el grafo
g = cargarGrafo()

@app.route("/")
def main_page():


	return render_template('personas_main.html',list=list)


@app.route("/usuarios")
def verUsuarios():
	list = []

	for u in g.subjects(predicate=RDF.type,object=usuarios_ns.type):
		dict = {}
		dict['id'] = g.value(u,usuarios_ns.Id)
		dict['tarjeta'] = g.value(u,usuarios_ns.Tarjeta)
		list+=[dict]

	return render_template('personas_sharedView.html',ref='/usuarios/crear',list=list)
@app.route("/vendedores")
def verVendedores():
	list = []

	for u in g.subjects(predicate=RDF.type,object=vendedores_ns.type):
		dict = {}
		dict['id'] = g.value(u,vendedores_ns.Id)
		dict['iban'] = g.value(u,vendedores_ns.IBAN)
		list+=[dict]

	return render_template('personas_sharedView.html',ref='/vendedores/crear',list=list)
@app.route("/transportistas")
def verTransportistas():
	list = []


	for u in g.subjects(predicate=RDF.type,object=transportistas_ns.type):
		dict = {}
		dict['id'] = g.value(u,transportistas_ns.Id)
		dict['nombre'] = g.value(u,transportistas_ns.NombreEmpresa)
		list+=[dict]

	return render_template('personas_sharedView.html',ref='/transportistas/crear',list=list)

@app.route("/usuarios/crear")
def crearUsuario():
	return render_template("personas_new_usuario.html")

@app.route("/vendedores/crear")
def crearVendedor():
	return render_template("personas_new_vendedor.html")

@app.route("/transportistas/crear")
def crearTransportista():
	return render_template("personas_new_transportista.html")

@app.route("/usuarios/submit")
def submitUsuario():
	id = request.args['id']
	credit = request.args['credit']

	g.add((usuarios_ns[id],RDF.type,usuarios_ns.type))
	g.add((usuarios_ns[id],usuarios_ns.Id,Literal(id)))
	g.add((usuarios_ns[id],usuarios_ns.Tarjeta,Literal(credit)))

	guardarGrafo()
	return redirect("/usuarios")

@app.route("/vendedores/submit")
def submitVendedor():
	id = request.args['id']
	iban = request.args['iban']

	g.add((vendedores_ns[id],RDF.type,vendedores_ns.type))
	g.add((vendedores_ns[id],vendedores_ns.Id,Literal(id)))
	g.add((vendedores_ns[id],vendedores_ns.IBAN,Literal(iban)))

	guardarGrafo()
	return redirect("/vendedores")

@app.route("/transportistas/submit")
def submitTransportista():
	id = request.args['id']
	nombre = request.args['nombre']

	g.add((transportistas_ns[id],RDF.type,transportistas_ns.type))
	g.add((transportistas_ns[id],transportistas_ns.Id,Literal(id)))
	g.add((transportistas_ns[id],transportistas_ns.NombreEmpresa,Literal(nombre)))

	guardarGrafo()
	return redirect("/transportistas")

@app.route("/usuarios/<id>/edit")
def editUsuario(id):
	pass

@app.route("/vendedores/<id>/edit")
def editVendedor(id):
	pass

@app.route("/transportistas/<id>/edit")
def editTransportista(id):
	pass

@app.route("/usuarios/<id>/delete")
def deleteUsuario(id):
	pass

@app.route("/vendedores/<id>/delete")
def deleteVendedor(id):
	pass

@app.route("/transportistas/<id>/delete")
def deleteTransportista(id):
	pass



def tidyup():
	#Instrucciones de parada
	guardarGrafo()

def start_server():
	app.run(host=host,port=port,debug=True)


if __name__ == "__main__":
	start_server()

