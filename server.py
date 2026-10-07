"""Echo server, sends nack every message it receives."""

from flask import Flask, request

app = Flask(__name__)


@app.route("/echo", methods=["POST"])
def echo():
    message = request.json["message"]
    print("Server received:", message)
    return {"echo": message}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
