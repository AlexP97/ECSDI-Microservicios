#! /bin/bash

trap "kill 0" EXIT

. directorio.config

python AgenteEmpaquetador.py --name Montserrat --open --dhost $directorio --port 7012 --host $centros &
python AgenteEnviador.py --name Montserrat --open --dhost $directorio --port 7002 --host $centros &

wait
