#! /bin/bash

trap "kill 0" EXIT

. directorio.config

python AgenteEmpaquetador.py --name Igualada --open --dhost $directorio --port 7011 --host $centros &
python AgenteEnviador.py --name Igualada --open --dhost $directorio --port 7001 --host $centros &

wait
