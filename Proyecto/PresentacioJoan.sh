#! /bin/bash

trap "kill 0" EXIT

. directorio.config

./removeTurtle.sh

python juegosPrueba.py

./TransportistaA.sh &
./TransportistaB.sh &
./TransportistaC.sh &

wait
