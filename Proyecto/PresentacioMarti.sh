#! /bin/bash

trap "kill 0" EXIT

. directorio.config

./removeTurtle.sh

python juegosPrueba.py

./Directorio.sh &

sleep 1.5

./VendedorA.sh &
./Tienda.sh &
./Pago.sh &

wait
