# -*- coding: utf-8 -*-
from imports import *
#Generador de juegos de prueba


def crearUsuario(id,tarjeta):
	g = Graph()
	g.add((usuarios_ns[id],RDF.type,usuarios_ns.type))
	g.add((usuarios_ns[id],usuarios_ns.Id,Literal(id)))
	g.add((usuarios_ns[id],usuarios_ns.Tarjeta,Literal(tarjeta)))
	return g

def crearTransportista(id,nombre):
	g = Graph()
	g.add((transportistas_ns[id],RDF.type,transportistas_ns.type))
	g.add((transportistas_ns[id],transportistas_ns.Id,Literal(id)))
	g.add((transportistas_ns[id],transportistas_ns.NombreEmpresa,Literal(nombre)))
	return g

def crearVendedor(id,iban):
	g = Graph()
	g.add((vendedores_ns[id],RDF.type,vendedores_ns.type))
	g.add((vendedores_ns[id],vendedores_ns.Id,Literal(id)))
	g.add((vendedores_ns[id],vendedores_ns.IBAN,Literal(iban)))
	return g

def crearPeso(idProducto,peso):
	g = Graph()

	prod = productos_ns[idProducto]

	g.add((prod,RDF.type,productos_ns.type))
	g.add((prod,productos_ns.Id,Literal(idProducto)))
	g.add((prod,productos_ns.Peso,Literal(peso)))
	
	return g
def crearCentro(id,direccion,cp):
	g = Graph()

	centro = centros_ns[id]
	g.add((centro,RDF.type,centros_ns.type))
	g.add((centro,centros_ns.Id,Literal(id)))
	add_localizacion_node(g,centro,centros_ns.Ubicadoen,direccion,cp)

	return g

def crearPesosCentro(id,pesos):
	g = Graph()

	centro = centros_ns[id]

	#nodo padre de la lista
	node =  centros_ns[id + '-listaProductos']

	#Anadimos el nodo padre de la coleccion de productos en todos los casos
	g.add((centro,centros_ns.Contiene,node))

	c = Collection(g,node)

	for pes in pesos:
		node = pes.subjects(RDF.type,productos_ns.type).next()
		g+=pes
		c.append(node)

	return g

def crearProductoPedido(idProductoPedido,idProducto,estado,fechaEnvio,centro):
	id = idProductoPedido
	g = Graph()
	g.add((productosPedido_ns[id],RDF.type,productos_ns.type))
	g.add((productosPedido_ns[id],productosPedido_ns.Id,Literal(id)))
	g.add((productosPedido_ns[id],productosPedido_ns.AsociadoAlProducto,productos_ns[idProducto]))
	if estado is not None: g.add((productosPedido_ns[id],productosPedido_ns.Estado,Literal(estado)))
	if fechaEnvio is not None: g.add((productosPedido_ns[id],productosPedido_ns.FechaEnvio,Literal(fechaEnvio)))
	if centro is not None: g.add((productosPedido_ns[id],productosPedido_ns.CentroAsignado,centros_ns[centro]))
	return g

def crearProductoEnvio(id):
	g = Graph()
	g.add((productos_ns[id],RDF.type,productos_ns.type))
	g.add((productos_ns[id],productos_ns.Id,Literal(id)))
	return g

def crearEnvioLote(id):
	g = Graph()
	g.add((envios_ns[id],RDF.type,envios_ns.type))
	g.add((envios_ns[id],envios_ns.Id,Literal(id)))
	return g


#Productos es una lista de grafos
def crearPedido(id,user_id,prioridad,fecha,importe,direccion,cp,productos):
	g = Graph()
	g.add((pedidos_ns[id],RDF.type,pedidos_ns.type))
	g.add((pedidos_ns[id],pedidos_ns.Id,Literal(id)))
	g.add((pedidos_ns[id],pedidos_ns.Hechopor,usuarios_ns[user_id]))
	g.add((pedidos_ns[id],pedidos_ns.Prioridad,Literal(prioridad)))
	g.add((pedidos_ns[id],pedidos_ns.Fecharealizacion,Literal(fecha)))
	g.add((pedidos_ns[id],pedidos_ns.Importetotal,Literal(importe)))

	add_localizacion_node(g,pedidos_ns[id],pedidos_ns.Tienedirecciondeentrega,direccion,cp)

	lista = pedidos_ns[id + '-ListaProductos']
	g.add((pedidos_ns[id],pedidos_ns.Contiene,lista))
	c = Collection(g,lista)

	for p in productos:
		node = p.subjects(RDF.type,productos_ns.type).next()
		g+=p
		c.append(node)

	return g

def crearEnvio(id,user_id,pedido_id,fecha,direccion,cp,productos,importeTotal,estado,prioridad,peso):
	g = Graph()

	#Generamos un id aleatorio
	envio_id = id

	#Anadimos el ID al envio
	g.add((envios_ns[envio_id],RDF.type,envios_ns.type))
	g.add((envios_ns[envio_id],envios_ns.Id,Literal(envio_id)))

	#Anadimos el usuario al envio
	user = usuarios_ns[user_id]
	g.add((envios_ns[envio_id],envios_ns.Hechopor,user))

	#Anadimos la referencia al pedido original
	pedido_uri = pedidos_ns[pedido_id]
	g.add((envios_ns[envio_id],envios_ns.Llevaacabo,pedido_uri))

	#fecha de realizacion
	g.add((envios_ns[envio_id],envios_ns.Fecharealizacion,Literal(fecha)))

	add_localizacion_node(g,envios_ns[id],envios_ns.Tienedirecciondeentrega,direccion,cp)

	#Anadimos el conjunto de productos al grafo de envio. Hay que crear un nodo no anonimo para la lista
	# o sino la libreria no funciona bien
	lista = envios_ns[envio_id + '-ListaProductos']
	g.add((envios_ns[envio_id],envios_ns.Contiene,lista))
	c = Collection(g,lista)


	for p in productos:
		node = p.subjects(RDF.type,productos_ns.type).next()
		g+=p
		c.append(node)

	#Anadimos el importe total
	g.add((envios_ns[envio_id],envios_ns.Importetotal,Literal(importeTotal)))

	g.add((envios_ns[envio_id],envios_ns.Prioridad,Literal(prioridad)))

	g.add((envios_ns[envio_id],envios_ns.EstadoEnvio,Literal(estado)))

	g.add((envios_ns[envio_id],envios_ns.Peso,Literal(peso)))

	return g

def crearLote(id,estado,ciudad,peso,envios,prioridad):

	g = Graph()

	#Anadimos el ID al envio
	g.add((lotes_ns[id],RDF.type,lotes_ns.type))
	g.add((lotes_ns[id],lotes_ns.Id,Literal(id)))
	g.add((lotes_ns[id],lotes_ns.Peso,Literal(peso)))
	g.add((lotes_ns[id],lotes_ns.Ciudad,Literal(ciudad)))
	g.add((lotes_ns[id],lotes_ns.Estadodellote,Literal(estado)))
	g.add((lotes_ns[id],lotes_ns.Prioridad,Literal(prioridad)))

	lista = lotes_ns[id + '-ListaEnvios']
	g.add((lotes_ns[id],lotes_ns.TieneEnvios,lista))
	c = Collection(g,lista)

	for e in envios:
		node = e.subjects(RDF.type,envios_ns.type).next()
		g+=e
		c.append(node)

	return g

def crearProductoExterno(id,nombre,importe,centros,vendedor):
	g = crearProducto(id,nombre,importe,centros)
	g.add((productos_ns[id],productos_ns.Esvendidopor,agenteVendedor_ns[vendedor]))
	g.add((productos_ns[id],productos_ns.EnVenta,Literal(True)))
	return g

def crearProducto(id,nombre,importe,centros):
	g = Graph()
	g.add((productos_ns[id],RDF.type,productos_ns.type))
	g.add((productos_ns[id],productos_ns.Id,Literal(id)))
	g.add((productos_ns[id],productos_ns.Nombre,Literal(nombre)))
	g.add((productos_ns[id],productos_ns.Importe,Literal(importe)))
	
	node = productos_ns[id + '-listaCentros']
	g.add((productos_ns[id],productos_ns.CentrosLogisticos,node))
	col = Collection(g,node)

	for centro in centros:
		col.append(centros_ns[centro])

	return g


def generarProductos():
	g = Graph()
	g+=crearProducto('Zanahorias','Zanahorias',10,['Igualada'])
	g+=crearProducto('Manzanas','Manzanas',20,['Igualada','Capellades'])
	g+=crearProducto('Peras','Peras',30,['Capellades'])
	g+=crearProductoExterno('Cacahuetes','Cacahuetes',50,['Igualada','Capellades'],'VendedorA')
	g.serialize('Datos/productos.turtle',format='turtle')

#Pedido de prueba sin enviar. Solo por el lote
def crearPedidoPrueba0():
	productos = []
	productos += [crearProductoPedido('Zanahorias0Pedido0','Zanahorias','Asignado',None,'Igualada')]
	productos += [crearProductoPedido('Peras0Pedido0','Peras','Asignado',None,'Capellades')]

	pedido = crearPedido('PedidoPrueba0','Adrian','Alta','1995-06-06',40,'Calle Falsa 0','08710',productos)

	return pedido

#Pedido de prueba ya enviado por la tienda externa
def crearPedidoPrueba1():
	productos = []
	productos += [crearProductoPedido('Manzanas0Pedido1','Manzanas','Enviado','1995-04-04',None)]
	productos += [crearProductoPedido('Manzanas1Pedido1','Manzanas','Enviado','1995-04-04',None)]

	pedido = crearPedido('PedidoPrueba1','Alex','Baja','1995-04-02',40,'Calle Alex 1','08100',productos)

	return pedido

#Pedido de prueba ya enviado por la tienda externa
def crearPedidoPrueba2():
	productos = []
	productos += [crearProductoPedido('Cacahuetes0Pedido2','Cacahuetes','Asignado','1995-04-04','Montserrat')]
	productos += [crearProductoPedido('Manzanas0Pedido2','Manzanas','Asignado','1995-04-04','Montserrat')]
	productos += [crearProductoPedido('Manzanas1Pedido2','Manzanas','Asignado','1995-04-04','Montserrat')]
	productos += [crearProductoPedido('Manzanas2Pedido2','Manzanas','Asignado','1995-04-04','Montserrat')]
	productos += [crearProductoPedido('Manzanas3Pedido2','Manzanas','Asignado','1995-04-04','Montserrat')]

	pedido = crearPedido('PedidoPrueba2','Joan','Baja','1995-04-02',90,'Av Balmes','08700',productos)

	return pedido


#Envio de prueba no enviado, solo tenemos sus lotes creados a la espera
def crearEnviosPrueba0():
	productos = []
	productos += [crearProductoEnvio('Zanahorias')]

	envio0 = crearEnvio('EnvioPrueba0.0','Adrian','PedidoPrueba0','1995-05-06','Calle Falsa 0','08710',productos,10,'EnLote','Inmediata',50)

	productos = []
	productos += [crearProductoEnvio('Peras')]

	envio1 = crearEnvio('EnvioPrueba0.1','Adrian','PedidoPrueba0','1995-05-06','Calle Falsa 0','08710',productos,30,'EnLote','Inmediata',100)

	#envio0 = Igualada
	#envio1 = Capellades

	envio0.serialize('Datos/Envios/Igualada.turtle',format='turtle')
	envio1.serialize('Datos/Envios/Capellades.turtle',format='turtle')

def crearEnviosPrueba1():

	productos = []
	productos += [crearProductoEnvio('Manzanas')]
	productos += [crearProductoEnvio('Manzanas')]

	envio0 = crearEnvio('EnvioPrueba1.0','Alex','PedidoPrueba1','1994-05-03','Calle Alex 1','08100',productos,40,'Enviado','Indefinida',150)

	envio0.serialize('AgenteUsuario/Envios/Alex.turtle',format="turtle")

def crearEnviosPrueba2():

	productos = []
	productos += [crearProductoEnvio('Cacahuetes')]
	productos += [crearProductoEnvio('Manzanas')]
	productos += [crearProductoEnvio('Manzanas')]
	productos += [crearProductoEnvio('Manzanas')]
	productos += [crearProductoEnvio('Manzanas')]

	envio2 = crearEnvio('EnvioPrueba2.0','Joan','PedidoPrueba2','1994-05-03','Av Balmes','08700',productos,90,'EnLote','Normal',500)

	envio2.serialize('Datos/Envios/Montserrat.turtle',format="turtle")
# Crea los lotes del pedido de prueba 0 en los 2 centros distintos
def crearLotesPrueba0():
	envios = []
	envios += [crearEnvioLote('EnvioPrueba0.0')]

	#Lote de igualada
	lote0 = crearLote('LotePrueba0.0','Idle','08710',50,envios,'Inmediata')

	envios = []
	envios += [crearEnvioLote('EnvioPrueba0.1')]
	#Lote de capellades
	lote1 = crearLote('LotePrueba0.1','Idle','08710',100,envios,'Inmediata')

	lote0.serialize('Datos/Lotes/Igualada.turtle',format='turtle')
	lote1.serialize('Datos/Lotes/Capellades.turtle',format='turtle')

def crearLotesPrueba2():
	envios = []
	envios += [crearEnvioLote('EnvioPrueba2.0')]

	#Lote de igualada
	lote2 = crearLote('LotePrueba2.0','Idle','08700',800,envios,'Normal')

	lote2.serialize('Datos/Lotes/Montserrat.turtle',format='turtle')

#Envio ya realizado por el centro. Servira para probar la devolucion
def generarInformacionCentros():
	crearEnviosPrueba0()
	crearEnviosPrueba1()
	crearEnviosPrueba2()
	crearLotesPrueba0()
	crearLotesPrueba2()

def anadirProductoCarrito(id,importe,nombre,cantidad):
	g = Graph()
	g.add((productos_ns[id], productos_ns.Id,Literal(id)))
	g.add((productos_ns[id], productos_ns.Importe,Literal(importe)))
	g.add((productos_ns[id], productos_ns.Nombre,Literal(nombre)))
	g.add((productos_ns[id], productos_ns.Cantidad,Literal(cantidad)))
	g.add((productos_ns[id], RDF.type, productos_ns.type))
	return g

def generarCarritoAlex():
	g = Graph()

	g+=anadirProductoCarrito('Peras',30,'Peras',5)
	g+=anadirProductoCarrito('Manzanas',20,'Manzanas',10)
	g+=anadirProductoCarrito('Zanahorias',10,'Zanahorias',1)

	g.serialize('AgenteUsuario/Carritos/Alex.turtle',format='turtle')

def generarCarritoAdrian():
	g = Graph()

	g+=anadirProductoCarrito('Cacahuetes',50,'Cacahuetes',3)

	g.serialize('AgenteUsuario/Carritos/Adrian.turtle',format='turtle')

def generarCarritoFalso():
	g = Graph()

	g+=anadirProductoCarrito('Peras',30,'Peras',5)
	g+=anadirProductoCarrito('Manzanas',20,'Manzanas',10)
	g+=anadirProductoCarrito('Zanahorias',10,'Zanahorias',1)

	g.serialize('AgenteUsuario/carritoFalso.turtle',format='turtle')

def generarPedidos():
	g = Graph()
	pedidoAlex = crearPedidoPrueba1()
	pedidoAdrian = crearPedidoPrueba0()
	pedidoJoan = crearPedidoPrueba2()

	g+=pedidoAlex
	g+=pedidoAdrian
	g+=pedidoJoan

	g.serialize('Datos/pedidos.turtle',format='turtle')

	pedidoAlex.serialize('AgenteUsuario/Pedidos/Alex.turtle',format='turtle')
	pedidoAdrian.serialize('AgenteUsuario/Pedidos/Adrian.turtle',format='turtle')

def generarCentros():
	centros = Graph()
	centros += crearCentro('Igualada','Avennida Pastor 30','08700')
	centros += crearCentro('Capellades','Abric Romani 1', '08711')
	centros += crearCentro('Montserrat','En el pico','07342')

	pesos = []
	pesos += [crearPeso('Zanahorias',50)]
	pesos += [crearPeso('Manzanas',200)]
	pesos += [crearPeso('Cacahuetes',25)]

	#Centro de igualada
	igualada  = crearPesosCentro('Igualada',pesos)

	pesos = []
	pesos += [crearPeso('Manzanas',200)]
	pesos += [crearPeso('Peras',100)]
	pesos += [crearPeso('Cacahuetes',25)]

	#Centro de capellades
	capellades = crearPesosCentro('Capellades',pesos)
	montserrat = crearPesosCentro('Montserrat',pesos)


	centros.serialize('Datos/centros.turtle',format='turtle')
	igualada.serialize('Datos/Pesos/Igualada.turtle',format='turtle')
	capellades.serialize('Datos/Pesos/Capellades.turtle',format='turtle')
	montserrat.serialize('Datos/Pesos/Montserrat.turtle', format='turtle')

def generarPersonas():
	g = Graph()
	g+= crearUsuario('Alex','TarjetaVISAAlex')
	g+= crearUsuario('Adrian','TarjetaMasterCardAdrian')
	g+= crearUsuario('Joan','Efectivo')

	g+=crearTransportista('TransportistaA','Transportes Jose')
	g+=crearTransportista('TransportistaB','Transvisa')
	g+=crearTransportista('TransportistaC','UPS')

	g+=crearVendedor('VendedorA','IBANVendedorA')

	g.serialize('Datos/personas.turtle',format='turtle')

def generarJuegos():
	generarCentros()
	generarPersonas()
	generarPedidos()
	generarProductos()
	generarInformacionCentros()
	generarCarritoAlex()
	generarCarritoAdrian()
	generarCarritoFalso()

if __name__ == '__main__':
	generarJuegos()