#!/bin/bash
set -e

# replicated log iteration 3

echo
echo "running harness tests (iterations 1, 2 and 3)"
python -m pytest -v test_harness.py

echo
if ! docker ps > /dev/null 2>&1; then
    echo "Docker is not running, try colima start or other tool to start the Docker."
    exit 1
fi

if docker compose version > /dev/null 2>&1; then
    COMPOSE="docker compose"
else
    COMPOSE="docker-compose"
fi

# start without secondary2, it joins later
$COMPOSE up -d --build master secondary1
sleep 3

# def send a message with write concern w: post <message> <w>
post() {
    curl -s -X POST localhost:8000/messages -H "Content-Type: application/json" \
         -d "{\"message\": \"$1\", \"w\": $2}"
    echo
}

echo
echo "msg1 w=1 (ok, only master):"
time post msg1 1

echo
echo "msg2 w=2 (ok, secondary1 is enough):"
time post msg2 2

echo
echo "msg3 w=3 (waits until secondary2 is up, runs in background):"
post msg3 3 &
sleep 1

echo
echo "msg4 w=1 (ok, not blocked by msg3):"
time post msg4 1

echo
echo "Messages right now (secondary2 is down):"
echo "master:     $(curl -s localhost:8000/messages)"
echo "secondary1: $(curl -s localhost:8001/messages)"

echo
echo "Starting secondary2..."
$COMPOSE up -d secondary2

echo
echo "Waiting for msg3 to finish..."
wait
sleep 10

echo
echo "Messages after secondary2 joined:"
echo "master:     $(curl -s localhost:8000/messages)"
echo "secondary1: $(curl -s localhost:8001/messages)"
echo "secondary2: $(curl -s localhost:8002/messages)"

echo
echo "Master retries:"
$COMPOSE logs master | grep -i "retry" | head -10

echo
echo "Secondary errors and duplicates:"
$COMPOSE logs secondary1 secondary2 | grep -iE "simulated|duplicate"

echo
$COMPOSE down
echo "done!"
