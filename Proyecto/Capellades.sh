#! /bin/bash

trap "kill 0" EXIT

. directorio.config

python AgenteEmpaquetador.py --name Capellades --open --dhost $directorio --port 7010 --host $centros &
python AgenteEnviador.py --name Capellades --open --dhost $directorio --port 7000 --host $centros &

wait
