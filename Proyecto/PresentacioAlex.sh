#! /bin/bash

trap "kill 0" EXIT

. directorio.config

./removeTurtle.sh

python juegosPrueba.py

./Montserrat.sh &
./Igualada.sh &
./Capellades.sh &

wait
