#! /bin/bash

trap "kill 0" EXIT

. directorio.config

python AgenteTransportista.py --name TransportistaA --open --dhost $directorio --port 8080 &

wait
