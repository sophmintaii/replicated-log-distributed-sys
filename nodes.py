import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class SecondaryNode:
    def __init__(self):
        self.messages = {}

    def receive(self, msg_id, message):
        if msg_id in self.messages:
            logging.info(f"Duplicate #{msg_id} '{message}', ignored")
        else:
            self.messages[msg_id] = message
            logging.info(f"Saved #{msg_id} '{message}'")
        return "ack"

    def list_msgs(self):
        result = []
        msg_id = 1
        while msg_id in self.messages:
            result.append(self.messages[msg_id])
            msg_id += 1
        return result


class MasterNode:
    def __init__(self, transport, secondaries, first_retry_delay=0.5, max_retry_delay=8):
        self.transport = transport
        self.secondaries = secondaries
        self.messages = []
        self.lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=50)
        self.first_retry_delay = first_retry_delay
        self.max_retry_delay = max_retry_delay

    def append_msg(self, message, w=None):
        if w is None:
            w = len(self.secondaries) + 1
        with self.lock:
            self.messages.append(message)
            msg_id = len(self.messages)
        logging.info(f"Appended #{msg_id} '{message}', replicating")

        futures = [self.pool.submit(self.replicate, secondary, msg_id, message)
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

    def replicate(self, secondary, msg_id, message):
        delay = self.first_retry_delay
        while True:
            try:
                return self.transport.send(self, secondary, msg_id, message)
            except Exception as error:
                logging.warning(f"#{msg_id} to {secondary} failed ({type(error).__name__}), retry in {delay}s")
                time.sleep(delay)
                delay = min(delay * 2, self.max_retry_delay)
 

    def list_msgs(self):
        return list(self.messages)
