#! /bin/bash

trap "kill 0" EXIT

. directorio.config

python AgenteTransportista.py --name TransportistaC --open --dhost $directorio --port 8082 --host $transportistas &

wait
