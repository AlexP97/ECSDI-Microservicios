#! /bin/bash

trap "kill 0" EXIT

. directorio.config

python AgenteTransportista.py --name TransportistaB --open --dhost $directorio --port 8081 --host $transportistas &

wait
