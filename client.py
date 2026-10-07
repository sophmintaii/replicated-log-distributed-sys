"""Echo client, sends a message to the server and prints the reply."""

import sys
import requests

message = sys.argv[1] if len(sys.argv) > 1 else "hello"

response = requests.post("http://localhost:8000/echo", json={"message": message})
response.raise_for_status()
print("Client got back:", response.json()["echo"])
