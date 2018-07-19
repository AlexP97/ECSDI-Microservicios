
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 15:58:13 2013

Esqueleto de agente usando los servicios web de Flask

/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente

Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente

Asume que el agente de registro esta en el puerto 9000

@author: alejandro
"""

from imports import *

__author__ = 'alejandro'

argumentos = getArguments(my_port=8007)
#Direcciones hardcodeadas (propia)
host = argumentos['host']
port = argumentos['port']

name = argumentos['name']

directorio_host = argumentos['dir_host']
directorio_port = argumentos['dir_port']

addr = argumentos['addr']

agn = getAgentNamespace()

#Objetos agente
AgenteOpinador = Agent('AgenteOpinador',agenteOpinador_ns[name],formatDir(addr,port) + '/comm',None)
DirectorioAgentes = Agent('DirectorioAgentes',agn.Directory,formatDir(directorio_host,directorio_port) + '/comm',None)

opiniones_db = 'Datos/opiniones.turtle'
opiniones = Graph()
productos_db = 'Datos/productos.turtle'
productos = Graph()

cola1 = Queue()

# Flask stuff
app = Flask(__name__,template_folder="AgenteOpinador/templates")

#Acciones. Este diccionario sera cargado con todos los procedimientos que hay que llamar dinamicamente 
# cuando llega un mensaje
actions = {}

#Carga los grafoos rdf de los distintos ficheros
def cargarGrafos():
    global opiniones
    global productos
    opiniones = Graph()
    productos = Graph()
    if os.path.isfile(opiniones_db):
        opiniones.parse(opiniones_db,format="turtle")
    if os.path.isfile(productos_db):
        productos.parse(productos_db,format="turtle")
    

def guardarGrafo(g,file):
    g.serialize(file,format="turtle")   

def guardarGrafoOpiniones():
    guardarGrafo(opiniones,opiniones_db)

@app.route("/")
def main():
    return render_template("main.html")

@app.route("/altaOpinion")
def altaOpinion():
    return 'ruta no definida'


def getProductosRecomendadosUsuario(user_uri):
    p = list(productos.subjects(predicate=RDF.type,object=productos_ns.type))
    try:
        p = random.sample(p,5)
    except ValueError:
        #la lista de productos sera la lista completa
        pass

    g = Graph()
    for prod in p:
        g+=expandirGrafoRec(productos,prod)

    return g

def enviarProductosRecomendadosUsuario(res,user_uri):

    obj = createAction(AgenteOpinador,'rebreRecomanacions')

    res.add((obj, RDF.type, agn.RecomendarProductos))
    
    msg = build_message(res,
        perf=ACL.inform,
        sender=AgenteOpinador.uri,
        content=obj)

    send_message_uri(msg,AgenteOpinador,DirectorioAgentes,agenteUsuario_ns.type,user_uri)

@app.route("/enviarRecomendaciones")
def generarRecomendacion():
    usuarios = get_all_uris(AgenteOpinador,DirectorioAgentes,agenteUsuario_ns.type)
    for user in usuarios:
        prods = getProductosRecomendadosUsuario(user)
        enviarProductosRecomendadosUsuario(prods,user)
    return redirect("/")


def getProductosAOpinarUsuario(usuario):
    #Buscar de opiniones y borrar los productos ya comprados de este
    g = Graph()
    g.add((productos_ns["999"],RDF.type,productos_ns.type))
    g.add((productos_ns["999"],productos_ns.Nombre,Literal('producto1aOpinar')))
    g.add((productos_ns["999"],productos_ns.Id,Literal('999')))
    
    g.add((productos_ns["998"],RDF.type,productos_ns.type))
    g.add((productos_ns["998"],productos_ns.Nombre,Literal('producto2aOpinar')))
    g.add((productos_ns["998"],productos_ns.Id,Literal('998')))
    
    g.add((productos_ns["997"],RDF.type,productos_ns.type))
    g.add((productos_ns["997"],productos_ns.Nombre,Literal('producto3aOpinar')))
    g.add((productos_ns["997"],productos_ns.Id,Literal('997')))
    return g


def pedirOpinionUsuario(usuario,grafo):
    obj = createAction(AgenteOpinador,'pedirOpinion')

    grafo.add((obj, RDF.type, agn.PedirOpiniones))
    
    msg = build_message(grafo,
        perf=ACL.request,
        sender=AgenteOpinador.uri,
        content=obj)

    send_message_uri(msg,AgenteOpinador,DirectorioAgentes,agenteUsuario_ns.type,usuario)

@app.route("/pedirOpinion")
def pedirOpinion():
    usuarios = get_all_uris(AgenteOpinador,DirectorioAgentes,agenteUsuario_ns.type)

    for u in usuarios:
        prods = getProductosAOpinarUsuario(u)
        pedirOpinionUsuario(u,prods)

    return redirect("/")

def nuevaOpinion(graph):
    global opiniones
    p = graph.subjects(predicate=RDF.type,object=opiniones_ns.type)

    add = Graph()
    for pe in p:
        add += expandirGrafoRec(graph,pe)

    opiniones+=add
    guardarGrafoOpiniones()
    return create_confirm(AgenteOpinador,None)


@app.route("/comm")
def comunicacion():

    cargarGrafos()
    
    # Extraemos el mensaje y creamos un grafo con él
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)
    msgdic = get_message_properties(gm)
    # Comprobamos que sea un mensaje FIPA ACL y que la performativa sea correcta
    if not msgdic:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = create_notUnderstood(AgenteOpinador,None)
    else:
        content = msgdic['content']
        # Averiguamos el tipo de la accion
        accion = gm.value(subject=content, predicate=RDF.type)

        #Llamada dinamica a la accion correspondiente
        if accion in actions:
            gr = actions[accion](gm)
        else:
            gr = create_notUnderstood(AgenteOpinador,None)

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
    register_message(AgenteOpinador,DirectorioAgentes,agenteOpinador_ns.type)

def registerActions():
    global actions
    actions[agn.DarOpinion] = nuevaOpinion




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
