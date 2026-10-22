import threading
import time
from nodes import MasterNode, SecondaryNode
from transport import MockedTransport


def timed(function, *args):
    """Runs function and returns how many seconds it took."""
    start = time.time()
    function(*args)
    return time.time() - start


def test_replication_is_blocking_and_parallel():
    """iteration 1"""
    transport = MockedTransport()
    secondary1 = SecondaryNode()
    secondary2 = SecondaryNode()
    master = MasterNode(transport, [secondary1, secondary2])

    # m1: secondary1 is slow (5s) -> master must wait 5s
    transport.set_delay(master, secondary1, 5)
    assert 5 <= timed(master.append_msg, "m1") < 5.5
    assert master.list_msgs() == ["m1"]

    # m2: secondary1 slow (5s) AND secondary2 slow (6s)
    # parallel -> ~6s (sequential would be 11s)
    transport.set_delay(master, secondary2, 6)
    assert 6 <= timed(master.append_msg, "m2") < 6.5
    assert master.list_msgs() == ["m1", "m2"]

    # m3: no delays -> no blocking
    transport.remove_delay(master, secondary1)
    transport.remove_delay(master, secondary2)
    assert timed(master.append_msg, "m3") < 0.5

    # every node has every message, in the same order
    assert master.list_msgs() == ["m1", "m2", "m3"]
    assert secondary1.list_msgs() == ["m1", "m2", "m3"]
    assert secondary2.list_msgs() == ["m1", "m2", "m3"]

def test_write_concern_and_eventual_consistency():
    """iteration 2"""
    transport = MockedTransport()
    secondary1 = SecondaryNode()
    secondary2 = SecondaryNode()
    master = MasterNode(transport, [secondary1, secondary2])
    transport.set_delay(master, secondary2, 3)

    # w=1: only the master -> returns immediately
    assert timed(master.append_msg, "m1", 1) < 0.5

    #  master has m1, slow secondary2 not yet
    assert master.list_msgs() == ["m1"]
    assert secondary2.list_msgs() == []

    # w=2: master + one secondary -> fast secondary1 is enough
    assert timed(master.append_msg, "m2", 2) < 0.5

    # w=3: needs slow secondary2 too -> blocks
    blocked_client = threading.Thread(target=master.append_msg, args=("m3", 3))
    blocked_client.start()
    time.sleep(0.1)
    # another client has w=1 -> not blocked
    assert timed(master.append_msg, "m4", 1) < 0.5
    time.sleep(0.1)
    assert master.list_msgs() == ["m1", "m2", "m3", "m4"]
    assert secondary1.list_msgs() == ["m1", "m2", "m3", "m4"]
    assert secondary2.list_msgs() == []
    # eventually client with w=3 catches up
    blocked_client.join()
    time.sleep(0.5)
    assert secondary2.list_msgs() == ["m1", "m2", "m3", "m4"]

def test_total_order_with_reordering():
    """iteration 2"""
    transport = MockedTransport()
    secondary1 = SecondaryNode()
    secondary2 = SecondaryNode()
    master = MasterNode(transport, [secondary1, secondary2])

    transport.reorder_messages(master, secondary1, messages_count=2)

    # m1 is held back by the network
    master.append_msg("m1")
    assert secondary1.list_msgs() == []

    # m2 is delivered before m1 but must be listed in correct order
    master.append_msg("m2")
    assert secondary1.list_msgs() == ["m1", "m2"]
    assert secondary2.list_msgs() == ["m1", "m2"]

def test_secondary_hides_messages_after_a_gap():
    """iteration 2"""
    secondary = SecondaryNode()

    # m3 missing -> do not show m4
    secondary.receive(1, "m1")
    secondary.receive(2, "m2")
    secondary.receive(4, "m4")
    assert secondary.list_msgs() == ["m1", "m2"]

    # m3 received -> now we show m4 too
    secondary.receive(3, "m3")
    assert secondary.list_msgs() == ["m1", "m2", "m3", "m4"]
