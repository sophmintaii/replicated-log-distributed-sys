import time
import logging
import requests

TIMEOUT = 10


class HttpTransport:
    """Used when running in Docker.

    Secondaries are URLs.
    """

    def send(self, master, secondary_url, msg_id, message):
        logging.info(f"Sending #{msg_id} '{message}' to {secondary_url}")
        response = requests.post(secondary_url + "/replicate",
                                 json={"id": msg_id, "message": message},
                                 timeout=TIMEOUT)
        response.raise_for_status()
        logging.info(f"ACK for #{msg_id} from {secondary_url}")
        return "ack"


class MockedTransport:
    """Fake network: used in tests.

    Secondaries are SecondaryNode objects.
    """

    def __init__(self):
        self.delays = {}
        self.reorder = {}
        self.held = {}
        self.down = set()
        self.errors_before_save = {}
        self.errors_after_save = {}

    def set_delay(self, master, secondary, seconds):
        self.delays[(master, secondary)] = seconds

    def remove_delay(self, master, secondary):
        self.delays.pop((master, secondary), None)

    def reorder_messages(self, master, secondary, messages_count=2):
        self.reorder[(master, secondary)] = messages_count
        self.held[(master, secondary)] = []

    def disconnect(self, master, secondary):
        self.down.add((master, secondary))

    def reconnect(self, master, secondary):
        self.down.discard((master, secondary))

    def fail_before_save(self, master, secondary, times=1):
        self.errors_before_save[(master, secondary)] = times
 
    def fail_after_save(self, master, secondary, times=1):
        self.errors_after_save[(master, secondary)] = times

    def use_one(self, counter, link):
        if counter.get(link, 0) > 0:
            counter[link] -= 1
            return True
        return False

    def deliver_reordered(self, link, secondary, msg_id, message):
        self.held[link].append((msg_id, message))
        if len(self.held[link]) < self.reorder[link]:
            return "held"
        for held_id, held_message in reversed(self.held[link]):
            secondary.receive(held_id, held_message)
        self.held[link] = []
        return "ack"

    def send(self, master, secondary, msg_id, message):
        link = (master, secondary)
        time.sleep(self.delays.get(link, 0))
 
        if link in self.down:
            raise ConnectionError("secondary is unavailable")
        if self.use_one(self.errors_before_save, link):
            raise ConnectionError("internal server error (before saving)")
 
        if link in self.reorder:
            result = self.deliver_reordered(link, secondary, msg_id, message)
        else:
            result = secondary.receive(msg_id, message)
 
        if self.use_one(self.errors_after_save, link):
            raise ConnectionError("internal server error (after saving)")
        return result
