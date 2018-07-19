
# -*- coding: utf-8 -*-
from imports import *

import difflib

__author__ = 'alejandro'

argumentos = getArguments(my_port=8002)

host = argumentos['host']
port = argumentos['port']

name = argumentos['name']

directorio_host = argumentos['dir_host']
directorio_port = argumentos['dir_port']

addr = argumentos['addr']

agn = getAgentNamespace()

#Objetos agente
AgenteBuscador = Agent('AgenteBuscador',agenteBuscador_ns[name],formatDir(addr,port) + '/comm',None)
DirectorioAgentes = Agent('DirectorioAgentes',agn.Directory,formatDir(directorio_host,directorio_port) + '/comm',None)


productos_db = 'Datos/productos.turtle'
productos = Graph()

peticiones_db = 'Datos/peticiones.turtle'
peticiones = Graph()

cola1 = Queue()

# Flask stuff
app = Flask(__name__,template_folder="SharedTemplates")

#Acciones. Este diccionario sera cargado con todos los procedimientos que hay que llamar dinamicamente 
# cuando llega un mensaje
actions = {}

#Carga los grafoos rdf de los distintos ficheros
def cargarGrafos():
    global productos
    productos = Graph()
    peticiones = Graph()
    if os.path.isfile(productos_db):
        productos.parse(productos_db,format="turtle")
    elif os.path.isfile(peticiones_db):
        peticiones.parse(peticiones_db, format="turtle")

def guardarGrafo(g,file):
    g.serialize(file,format="turtle")   

def guardarGrafoProductos():
    guardarGrafo(productos,productos_db)

def guardarGrafoPeticiones():
    guardarGrafo(peticiones,peticiones_db)

@app.route("/")
def hola():
    return "soy el agente buscador, hola!"


def buscarProductos(graph):
    global productos
    cargarGrafos()
    g = Graph()
    nuevaPeticion(graph)

    # Nombre equivalente
    for pe in graph.subjects(predicate=RDF.type, object=peticiones_ns.type):
        busqueda = graph.value(subject=pe,predicate=peticiones_ns.Busqueda)
        for p in productos.subjects(predicate=RDF.type, object=productos_ns.type):
            nombre = productos.value(subject=p,predicate=productos_ns.Nombre)
            if nombre == busqueda:
                g += expandirGrafoRec(productos,p)
    return g 


def nuevaPeticion(graph):
    global peticiones
    p = graph.subjects(predicate=RDF.type,object=peticiones_ns.type)
    save = Graph()
    for pe in p:
        save+= expandirGrafoRec(graph,pe)

    peticiones+=save
    guardarGrafoPeticiones()


@app.route('/Info')
def info():
	"""
	Entrada que da informacion sobre el agente a traves de una pagina web
	"""

	return render_template('info.html', nmess=0, graph=productos.serialize(format='turtle'))

@app.route("/comm")
def comunicacion():

    cargarGrafos()
    
    # Extraemos el mensaje y creamos un grafo con él
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)
    # Comprobamos que sea un mensaje FIPA ACL y que la performativa sea correcta
    if not msgdic or msgdic['performative'] != ACL.request:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = create_notUnderstood(AgenteBuscador,None)
    else:
        content = msgdic['content']
        # Averiguamos el tipo de la accion
        accion = gm.value(subject=content, predicate=RDF.type)

        #Llamada dinamica a la accion correspondiente
        if accion in actions:
            gr = actions[accion](gm)
        else:
            gr = create_notUnderstood(AgenteBuscador,None)

    return gr.serialize(format='xml')



@app.route("/Stop")
def stop():
    """
    Entrypoint que para el agente

    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"


def tidyup():
    """
    Acciones previas a parar el agente

    """
    pass


def agentbehavior1(cola):
    """
    Un comportamiento del agente

    :return:
    """
    pass

def init_agent():
    register_message(AgenteBuscador,DirectorioAgentes,agenteBuscador_ns.type)

def registerActions():
    global actions
    actions[agn.peticionBusqueda] = buscarProductos
    #actions[agn.VendedorNuevoProducto] = nuevaDevolucion




if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1, args=(cola1,))
    ab1.start()

    registerActions()

    cargarGrafos()
    init_agent()
    # Ponemos en marcha el servidor
    app.run(host=host, port=port,debug=True)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')
