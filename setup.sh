#!/bin/bash
set -e

# create venv and set it up
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt

# start echo server
python -u server.py > server.log 2>&1 &
SERVER_PID=$!
sleep 2

# send messages from client
python client.py "hello, world!"
python client.py "replicated log"

# stopping the server
kill $SERVER_PID

echo "done!"
