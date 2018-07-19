import sys
from rdflib import Namespace

agente_prefix = 'http://www.agentes.org/'
tienda_prefix = 'http://www.tienda.org/'
agn = Namespace(agente_prefix)
'''
ns_agentes = {
	'AgenteVendedorExterno':agn.Vendedor,
	'AgenteUsuario':agn.Usuario,
	'AgenteTransportista':agn.Transportista,
	'AgenteServicioPago':agn.Pago,
	'AgenteAdmisor':agn.Admisor,
	'AgenteDevolvedor':agn.Devolvedor,
	'AgenteEnviador':agn.Enviador,
	'AgenteMonetario':agn.Monetario,
	'AgenteReceptor':agn.Receptor,
	'AgenteBuscador':agn.Buscador,
	'AgenteEmpaquetador':agn.Empaquetador,
	'AgenteOpinador':agn.Opinador
}
'''
ns_agentes = {
	'AgenteDirectorio':agente_prefix + 'Directorio',
	'AgenteVendedorExterno':agente_prefix + 'Vendedor',
	'AgenteUsuario':agente_prefix + 'Usuario',
	'AgenteTransportista':agente_prefix + 'Transportista',
	'AgenteServicioPago':agente_prefix + 'Pago',
	'AgenteAdmisor':agente_prefix + 'Admisor',
	'AgenteDevolvedor':agente_prefix + 'Devolvedor',
	'AgenteEnviador':agente_prefix + 'Enviador',
	'AgenteMonetario':agente_prefix + 'Monetario',
	'AgenteReceptor':agente_prefix + 'Receptor',
	'AgenteBuscador':agente_prefix + 'Buscador',
	'AgenteEmpaquetador':agente_prefix + 'Empaquetador',	
	'AgenteOpinador':agente_prefix + 'Opinador'
}

ns_bases = {
	'Productos':tienda_prefix + 'Productos',
	'Vendedores':tienda_prefix + 'Vendedores',
	'Usuarios':tienda_prefix + 'Usuarios',
	'Pedidos':tienda_prefix + 'Pedidos',
	'Pesos':tienda_prefix + 'Pesos',
	'Envios':tienda_prefix + 'Envios',
	'Lotes':tienda_prefix + 'Lotes',
	'Pagos':tienda_prefix + 'Pagos',
	'Devoluciones':tienda_prefix + 'Devoluciones',
	'Transportistas':tienda_prefix + 'Transportistas',
	'Opiniones':tienda_prefix + 'Opiniones',
	'Ofertas':tienda_prefix + 'Ofertas', #de transporte
	'Peticiones':tienda_prefix + 'Peticiones', #de busqueda
	'Centros':tienda_prefix + 'Centros', #Centros logisticos
	'Direcciones':tienda_prefix + 'Direcciones', #Direcciones de entrega o de centros
	'Recomendaciones':tienda_prefix + 'Recomendaciones', #Recomendaciones de productos
	'Transacciones':tienda_prefix + 'Transacciones',
	'ProductosPedido':tienda_prefix + 'ProductosPedido'
}

def createAction(Agent,actionName):
	return agn[Agent.name + '-' + actionName]

def getAgentNamespace():
	return Namespace(agente_prefix)

def getNamespace(name):
	if (name in ns_agentes):
		return Namespace(ns_agentes[name] + '#')
	if (name in ns_bases):
		return Namespace(ns_bases[name] + '#')
	raise Exception('Namespace no encontrado')

directorio_ns = getNamespace('AgenteDirectorio')
agenteVendedor_ns = getNamespace('AgenteVendedorExterno')
agenteUsuario_ns = getNamespace('AgenteUsuario')
agenteTransportista_ns = getNamespace('AgenteTransportista')
agenteServicioPago_ns = getNamespace('AgenteServicioPago')
agenteAdmisor_ns = getNamespace('AgenteAdmisor')
agenteDevolvedor_ns = getNamespace('AgenteDevolvedor')
agenteEnviador_ns = getNamespace('AgenteEnviador')
agenteMonetario_ns = getNamespace('AgenteMonetario')
agenteReceptor_ns = getNamespace('AgenteReceptor')
agenteBuscador_ns = getNamespace('AgenteBuscador')
agenteEmpaquetador_ns = getNamespace('AgenteEmpaquetador')
agenteOpinador_ns = getNamespace('AgenteOpinador')

productos_ns = getNamespace('Productos')
vendedores_ns = getNamespace('AgenteVendedorExterno')
usuarios_ns = getNamespace('AgenteUsuario')
pedidos_ns = getNamespace('Pedidos')
pesos_ns = getNamespace('Pesos')
envios_ns = getNamespace('Envios')
lotes_ns = getNamespace('Lotes')
pagos_ns = getNamespace('Pagos')
devoluciones_ns = getNamespace('Devoluciones')
transportistas_ns = getNamespace('AgenteTransportista')
opiniones_ns = getNamespace('Opiniones')
ofertas_ns = getNamespace('Ofertas')
peticiones_ns = getNamespace('Peticiones')
centros_ns = getNamespace('Centros')
direcciones_ns = getNamespace('Direcciones')
recomendaciones_ns = getNamespace('Recomendaciones')
transacciones_ns = getNamespace('Transacciones')
productosPedido_ns = getNamespace('ProductosPedido')

if __name__ == "__main__":
	pass