trap "kill 0" EXIT

python editorCentrosLogisticos.py &
python AgenteUsuario.py &
python AgenteAdmisor.py &
python AgenteBuscador.py &
python AgenteEmpaquetador.py --port 8050 --name Vallecas &
python AgenteEmpaquetador.py --port 8051 --name Capellades &
python AgenteOpinador.py &
python AgenteReceptor.py &
python AgenteVendedorExterno.py &

wait