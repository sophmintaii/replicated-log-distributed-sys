"""Connects HTTP to MasterNode"""

import os
import logging
from concurrent.futures import ThreadPoolExecutor
import requests
from flask import Flask, request
from nodes import MasterNode
from transport import HttpTransport

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
app = Flask(__name__)

messages = []
SECONDARIES = [url for url in os.environ.get("SECONDARIES", "").split(",") if url]
MAX_W = len(SECONDARIES) + 1

master = MasterNode(HttpTransport(), SECONDARIES)

@app.route("/messages", methods=["GET"])
def list_messages():
    return {"messages": master.list_msgs()}


@app.route("/messages", methods=["POST"])
def append_message():
    message = request.json["message"]
    w = int(request.json.get("w", MAX_W))
    if not 1 <= w <= MAX_W:
        return {"error": f"w must be between 1 and {MAX_W}"}, 400
    msg_id = master.append_msg(message, w)
    return {"status": "ok", "id": msg_id}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
