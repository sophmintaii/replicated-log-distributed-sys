"""Secondary node, stores messages from the master and serves them."""

import os
import time
import logging
from flask import Flask, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
app = Flask(__name__)

messages = []
DELAY = int(os.environ.get("DELAY", 0)) # for testing without harness test


@app.route("/messages", methods=["GET"])
def list_messages():
    return {"messages": messages}


@app.route("/replicate", methods=["POST"])
def replicate():
    message = request.json["message"]
    logging.info(f"Got '{message}' from master, sleeping {DELAY}s")
    time.sleep(DELAY)
    messages.append(message)
    logging.info(f"Saved '{message}', sending ACK")
    return {"status": "ack"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))