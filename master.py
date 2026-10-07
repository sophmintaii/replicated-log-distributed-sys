"""Master node, appends messages and replicates them to all the secondaries"""

import os
import logging
from concurrent.futures import ThreadPoolExecutor
import requests
from flask import Flask, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
app = Flask(__name__)

messages = []
SECONDARIES = [url for url in os.environ.get("SECONDARIES", "").split(",") if url]


def send_to_secondary(url, message):
    logging.info(f"Sending '{message}' to {url}")
    requests.post(url + "/replicate", json={"message": message})
    logging.info(f"ACK from {url}")


@app.route("/messages", methods=["GET"])
def list_messages():
    return {"messages": messages}


@app.route("/messages", methods=["POST"])
def append_message():
    message = request.json["message"]
    messages.append(message)
    logging.info(f"Appended '{message}', replicating")

    with ThreadPoolExecutor() as pool:
        for url in SECONDARIES:
            pool.submit(send_to_secondary, url, message)

    logging.info(f"All ACKs received for '{message}'")
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
