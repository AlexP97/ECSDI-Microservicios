#!/usr/bin/env bash
python AgenteAdmisor.py &
python AgenteBuscador.py &
python AgenteEmpaquetador.py &
python AgenteOpinador.py &
python AgenteReceptor.py &
python AgenteUsuario.py &
python AgenteVendedorExterno.py &
python editorCentrosLogisticos.py &
#Matar todos los procesos
# pkill -P $$
