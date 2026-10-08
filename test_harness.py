import time
from nodes import MasterNode, SecondaryNode
from transport import MockedTransport


def timed(function, *args):
    """Runs function and returns how many seconds it took."""
    start = time.time()
    function(*args)
    return time.time() - start


def test_replication_is_blocking_and_parallel():
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
