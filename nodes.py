import logging
from concurrent.futures import ThreadPoolExecutor


class SecondaryNode:
    def __init__(self):
        self.messages = []

    def receive(self, message):
        self.messages.append(message)
        logging.info(f"Saved '{message}'")
        return "ack"

    def list_msgs(self):
        return list(self.messages)


class MasterNode:
    def __init__(self, transport, secondaries):
        self.transport = transport
        self.secondaries = secondaries
        self.messages = []

    def append_msg(self, message):
        self.messages.append(message)
        logging.info(f"Appended '{message}', replicating")

        with ThreadPoolExecutor() as pool:
            for secondary in self.secondaries:
                pool.submit(self.transport.send, self, secondary, message)

        logging.info(f"All ACKs received for '{message}'")

    def list_msgs(self):
        return list(self.messages)
