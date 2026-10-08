"""Connects SecondaryNode to HTTP."""

import os
import time
import logging
from flask import Flask, request
from nodes import SecondaryNode

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
app = Flask(__name__)

messages = []
DELAY = int(os.environ.get("DELAY", 0))  # for testing without harness test
secondary = SecondaryNode()


@app.route("/messages", methods=["GET"])
def list_messages():
    return {"messages": secondary.list_msgs()}


@app.route("/replicate", methods=["POST"])
def replicate():
    message = request.json["message"]
    logging.info(f"Got '{message}' from master, sleeping {DELAY}s")
    time.sleep(DELAY)
    messages.append(message)
    return {"status": secondary.receive(message)}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
