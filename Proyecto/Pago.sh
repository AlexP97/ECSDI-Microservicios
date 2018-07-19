#! /bin/bash

trap "kill 0" EXIT

. directorio.config

python ServicioPago.py --dhost $directorio --host $directorio --open --host $directorio  &

wait
