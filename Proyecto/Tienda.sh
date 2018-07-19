#! /bin/bash

trap "kill 0" EXIT

. directorio.config

python AgenteAdmisor.py --dhost $directorio --open --host $directorio &
python AgenteBuscador.py --dhost $directorio --open --host $directorio &
python AgenteDevolvedor.py --dhost $directorio --open --host $directorio &
python AgenteMonetario.py --dhost $directorio --open --host $directorio &
python AgenteOpinador.py --dhost $directorio --open --host $directorio &
python AgenteReceptor.py --dhost $directorio --open --host $directorio &

wait
