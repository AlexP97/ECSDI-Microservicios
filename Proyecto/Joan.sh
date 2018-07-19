#! /bin/bash

trap "kill 0" EXIT

. directorio.config

#python AgenteUsuario.py --name Joan --open --dhost $directorio --port 8002 &
python AgenteUsuario.py --name Joan --open --dhost $directorio --port 8002 --host $usuarios &

wait
