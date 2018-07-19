#! /bin/bash

trap "kill 0" EXIT

. directorio.config

./removeTurtle.sh

python juegosPrueba.py

./Joan.sh &
./Alex.sh &
./Adrian.sh &

wait
