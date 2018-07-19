# -*- coding: utf-8 -*-
from imports import *

__author__ = 'adrian'

#Cambiamos la ruta por defecto de los templates para que sea dentro de los ficheros del agente
app = Flask(__name__,template_folder="AgenteServicioPago/templates")

argumentos = getArguments(my_port=8011)

host = argumentos['host']
port = argumentos['port']

name = argumentos['name']

directorio_host = argumentos['dir_host']
directorio_port = argumentos['dir_port']

addr = argumentos['addr']


#Espacio de nombres para los productos y los agentes
agn = getAgentNamespace()


ServicioPago = Agent('AgenteServicioPago',agenteServicioPago_ns[name],formatDir(addr,port) + '/comm',None)
DirectorioAgentes = Agent('DirectorioAgentes',agn.Directory,formatDir(directorio_host,directorio_port) + '/comm',None)

pagos = Graph()
pagos_db = 'AgenteServicioPago/pagos.turtle'

def init_agent():
    register_message(ServicioPago,DirectorioAgentes,agenteServicioPago_ns.type)

#Carga los grafoos rdf de los distintos ficheros
def cargarGrafo():
    global pagos
    pagos = Graph()
    if os.path.isfile(pagos_db):
        pagos.parse(pagos_db,format="turtle")


def guardarGrafo(g,file):
    g.serialize(file,format="turtle")   

def guardarGrafoPagos():
    guardarGrafo(pagos,pagos_db)


#Acciones. Este diccionario sera cargado con todos los procedimientos que hay que llamar dinamicamente 
# cuando llega un mensaje
actions = {}

@app.route("/comm")
def comunicacion():
    cargarGrafo()
    # Extraemos el mensaje y creamos un grafo con él
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)
    msgdic = get_message_properties(gm)

    # Comprobamos que sea un mensaje FIPA ACL y que la performativa sea correcta
    if not msgdic:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = create_notUnderstood(ServicioPago,None)
    else:
        content = msgdic['content']
        # Averiguamos el tipo de la accion
        accion = gm.value(subject=content, predicate=RDF.type)

        #Llamada dinamica a la accion correspondiente
        if accion in actions:
            gr = actions[accion](gm)
        else:
            gr = create_notUnderstood(ServicioPago,None)

    return gr.serialize(format='xml')

def pedirPago(graph):
    global pagos
    cargarGrafo()
    add = Graph()
    for pago in graph.subjects(RDF.type,transacciones_ns.type):
        add+=expandirGrafoRec(graph,pago)

    pagos+=add
    guardarGrafoPagos()

    return create_confirm(ServicioPago)

@app.route("/")
def getPagos():
   
    list = []
    for p in pagos.subjects(predicate=RDF.type,object=transacciones_ns.type):
        list+=[transaccion_a_dict(pagos,p)]

    return render_template('lista_pagos.html',list=list)


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
    global cola1
    cola1.put(0)
    pass

def getPagos(graph):
    pass

def registerActions():
    global actions
    actions[agn.MonetarioPedirPago] = pedirPago

if __name__ == "__main__":
    registerActions()
    cargarGrafo()
    init_agent()
    # Ponemos en marcha el servidor
    app.run(host=host, port=port, debug=True)
