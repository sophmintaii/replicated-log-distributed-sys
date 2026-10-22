import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class SecondaryNode:
    def __init__(self):
        self.messages = {}

    def receive(self, msg_id, message):
        self.messages[msg_id] = message
        logging.info(f"Saved '{message}'")
        return "ack"

    def list_msgs(self):
        result = []
        msg_id = 1
        while msg_id in self.messages:
            result.append(self.messages[msg_id])
            msg_id += 1
        return result


class MasterNode:
    def __init__(self, transport, secondaries):
        self.transport = transport
        self.secondaries = secondaries
        self.messages = []
        self.lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=50)

    def append_msg(self, message, w=None):
        if w is None:
            w = len(self.secondaries) + 1
        with self.lock:
            self.messages.append(message)
            msg_id = len(self.messages)
        logging.info(f"Appended #{msg_id} '{message}', replicating")

        futures = [self.pool.submit(self.transport.send, self, secondary, msg_id, message) 
                   for secondary in self.secondaries]

        acks_needed = w - 1
        acks = 0
        if acks_needed > 0:
            for _ in as_completed(futures):
                acks += 1
                if acks == acks_needed:
                    break

        logging.info(f"#{msg_id}: got {acks} ACK(s) from secondaries")
        return msg_id

    def list_msgs(self):
        return list(self.messages)
