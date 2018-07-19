trap "kill 0" EXIT

./removeTurtle.sh

python DirectorioAgentes.py --port 8000 &

wait