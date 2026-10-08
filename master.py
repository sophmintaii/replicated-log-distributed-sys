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
master = MasterNode(HttpTransport(), SECONDARIES)

@app.route("/messages", methods=["GET"])
def list_messages():
    return {"messages": master.list_msgs()}


@app.route("/messages", methods=["POST"])
def append_message():
    master.append_msg(request.json["message"])
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
