#! /bin/bash

trap "kill 0" EXIT

. directorio.config

python AgenteUsuario.py --name Alex --dhost $directorio --port 8000 --open --host $usuarios &

wait
