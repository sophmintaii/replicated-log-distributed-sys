#!/bin/bash
set -e

# replicated log iteration 2

echo
echo "running harness tests (iterations 1 and 2)"
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

$COMPOSE up -d --build
sleep 3

# def send a message with write concern w: post <message> <w>
post() {
    curl -s -X POST localhost:8000/messages -H "Content-Type: application/json" \
         -d "{\"message\": \"$1\", \"w\": $2}"
    echo
}

echo
echo "msg1 w=1 (fast, only master):"
time post msg1 1

echo
echo "msg2 w=2 (fast, secondary1 is enough):"
time post msg2 2

echo
echo "msg3 w=3 (blocks appx 10s because of secondary2, runs in background):"
post msg3 3 &
sleep 1

echo
echo "msg4 w=1 (not blocked by msg3):"
time post msg4 1

echo
echo "Messages right now (secondary2 is behind):"
echo "master:     $(curl -s localhost:8000/messages)"
echo "secondary1: $(curl -s localhost:8001/messages)"
echo "secondary2: $(curl -s localhost:8002/messages)"

echo
echo "Waiting for msg3 to finish..."
wait
sleep 2

echo
echo "Messages after waiting:"
echo "master:     $(curl -s localhost:8000/messages)"
echo "secondary1: $(curl -s localhost:8001/messages)"
echo "secondary2: $(curl -s localhost:8002/messages)"

echo
echo "Master logs:"
$COMPOSE logs master | grep -E "Appended|Sending|ACK"

echo
$COMPOSE down
echo "done!"
