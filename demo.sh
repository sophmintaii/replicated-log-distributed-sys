#!/bin/bash
set -e

# create venv and set it up
# python3 -m venv venv
# source venv/bin/activate
# pip install -q -r requirements.txt

# replicated log iteration 1
if ! docker ps > /dev/null 2>&1; then
    echo "Docker is not running, try colima start or other tool to start the Docker."
    exit 1
fi

if docker compose version > /dev/null 2>&1; then
    COMPOSE="docker compose"
else
    COMPOSE="docker-compose"
fi

$COMPOSE up -d --build
sleep 3

echo
echo "Sending m1 to master"
time curl -s -X POST localhost:8000/messages -H "Content-Type: application/json" -d '{"message":"m1"}'
echo

echo
echo "Messages on each node (all contain m1):"
echo "master:     $(curl -s localhost:8000/messages)"
echo "secondary1: $(curl -s localhost:8001/messages)"
echo "secondary2: $(curl -s localhost:8002/messages)"

echo
echo "Master logs:"
$COMPOSE logs master | grep -E "Appended|Sending|ACK"

echo
$COMPOSE down
echo "done!"
