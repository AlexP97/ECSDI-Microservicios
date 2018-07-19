import json
import sys

gestor_direcciones = 'direcciones.json'

def formatDir(host,port):
	return 'http://%s:%d' % (host, port)

def get_data():
	data = {}
	data['agente_usuario'] = {
		'host':'localhost',
		'port':8000
	}
	data['agente_receptor'] = {
		'host':'localhost',
		'port':8000
	}
	data['agente_admisor'] = {
		'host':'localhost',
		'port':8000
	}
	data['agente_vendedorExterno'] = {
		'host':'localhost',
		'port':8000

	}
	return data


def write_json(file,data):
	with open(file,'w') as out:
		json.dump(data,out,indent=4)

def read_json(file):
	data = None
	with open(file,'r') as f:
		data = json.load(f)
	return data

def getDirAgenteUsuario():
	data = read_json(gestor_direcciones)
	return data['agente_usuario']

def getDirAgenteReceptor():
	data = read_json(gestor_direcciones)
	return data['agente_receptor']

def getDirAgenteAdmisor():
	data = read_json(gestor_direcciones)
	return data['agente_admisor']
def getDirAgenteVendedorExterno():
	data = read_json(gestor_direcciones)
	return data['agente_vendedorExterno']
def getDirAgenteMonetario():
	data = read_json(gestor_direcciones)
	return data['agente_monetario']
def getDirServicioPago():
	data = read_json(gestor_direcciones)
	return data['servicio_pago']

if __name__ == "__main__":
	output_file = None
	if (len(sys.argv) < 2):
		output_file = gestor_direcciones
	else:
		output_file = sys.argv[1]
	data = get_data()
	write_json(output_file,data)
	print ("Successfully wrote the json config file into") , output_file
	print ("The json structure is the following: ")
	json = read_json(output_file)
	print (json)
