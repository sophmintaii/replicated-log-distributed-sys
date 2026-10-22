import time
import logging
import requests


class HttpTransport:
    """Used when running in Docker.

    Secondaries are URLs.
    """

    def send(self, master, secondary_url, msg_id, message):
        logging.info(f"Sending #{msg_id} '{message}' to {secondary_url}")
        requests.post(secondary_url + "/replicate", json={"id": msg_id, "message": message})
        logging.info(f"ACK for #{msg_id} from {secondary_url}")


class MockedTransport:
    """Fake network: used in tests.

    Secondaries are SecondaryNode objects.
    """

    def __init__(self):
        self.delays = {}
        self.reorder = {}
        self.held = {}

    def set_delay(self, master, secondary, seconds):
        self.delays[(master, secondary)] = seconds

    def remove_delay(self, master, secondary):
        self.delays.pop((master, secondary), None)

    def reorder_messages(self, master, secondary, messages_count=2):
        self.reorder[(master, secondary)] = messages_count
        self.held[(master, secondary)] = []

    def send(self, master, secondary, msg_id, message):
        link = (master, secondary)
        time.sleep(self.delays.get(link, 0))

        if link not in self.reorder:
            return secondary.receive(msg_id, message)

        # simulate reordering
        self.held[link].append((msg_id, message))
        if len(self.held[link]) < self.reorder[link]:
            return "held"

        for held_id, held_message in reversed(self.held[link]):
            secondary.receive(held_id, held_message)
        self.held[link] = []
        return "ack"
