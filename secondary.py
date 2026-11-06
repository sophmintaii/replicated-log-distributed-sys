"""Connects SecondaryNode to HTTP."""

import os
import random
import time
import logging
from flask import Flask, request
from nodes import SecondaryNode

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
app = Flask(__name__)

messages = []
DELAY = int(os.environ.get("DELAY", 0))  # for testing without harness test
ERROR_RATE = float(os.environ.get("ERROR_RATE", 0))
secondary = SecondaryNode()


@app.route("/messages", methods=["GET"])
def list_messages():
    return {"messages": secondary.list_msgs()}


@app.route("/replicate", methods=["POST"])
def replicate():
    msg_id = request.json["id"]
    message = request.json["message"]
    logging.info(f"Got #{msg_id} '{message}' from master, sleeping {DELAY}s")
    time.sleep(DELAY)

    if random.random() < ERROR_RATE:
        logging.info(f"Simulated error for #{msg_id} BEFORE saving")
        return {"error": "simulated failure"}, 500

    secondary.receive(msg_id, message)

    if random.random() < ERROR_RATE:
        logging.info(f"Simulated error for #{msg_id} AFTER saving")
        return {"error": "simulated failure"}, 500

    return {"status": "ack"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
