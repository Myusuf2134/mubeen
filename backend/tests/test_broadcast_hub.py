"""Unit tests for BroadcastHub — written before implementation (MB-011).

BroadcastHub methods are all synchronous, so these are plain sync tests.
asyncio.Queue.put_nowait / get_nowait work without a running event loop in
Python 3.12.
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

from mubeen.services.broadcast import BroadcastHub


def test_subscribe_then_publish_delivers() -> None:
    hub = BroadcastHub()
    mid = uuid4()
    q = hub.subscribe(mid)
    hub.publish(mid, "msg")
    assert q.get_nowait() == "msg"


def test_publish_fans_out_to_n_subscribers() -> None:
    hub = BroadcastHub()
    mid = uuid4()
    queues = [hub.subscribe(mid) for _ in range(5)]
    hub.publish(mid, "broadcast")
    for q in queues:
        assert q.get_nowait() == "broadcast"


def test_channel_isolation_publish_to_a_never_reaches_b() -> None:
    hub = BroadcastHub()
    mid_a = uuid4()
    mid_b = uuid4()
    qa = hub.subscribe(mid_a)
    qb = hub.subscribe(mid_b)
    hub.publish(mid_a, "only_a")
    assert qa.get_nowait() == "only_a"
    assert qb.empty()


def test_publish_with_zero_subscribers_does_not_raise() -> None:
    hub = BroadcastHub()
    hub.publish(uuid4(), "msg")  # no subscribers; must not raise


def test_unsubscribe_stops_delivery_and_count_returns_to_zero() -> None:
    hub = BroadcastHub()
    mid = uuid4()
    q = hub.subscribe(mid)
    hub.unsubscribe(mid, q)
    hub.publish(mid, "msg")
    assert q.empty()
    assert hub.subscriber_count(mid) == 0


def test_unsubscribe_unknown_queue_is_idempotent() -> None:
    hub = BroadcastHub()
    mid = uuid4()
    orphan = asyncio.Queue()
    hub.unsubscribe(mid, orphan)  # channel doesn't even exist — must not raise
    hub.subscribe(mid)
    hub.unsubscribe(mid, orphan)  # channel exists but queue is not in it — must not raise


def test_double_unsubscribe_does_not_raise() -> None:
    hub = BroadcastHub()
    mid = uuid4()
    q = hub.subscribe(mid)
    hub.unsubscribe(mid, q)
    hub.unsubscribe(mid, q)  # second call — must not raise


def test_empty_channel_key_removed_after_last_subscriber_leaves() -> None:
    hub = BroadcastHub()
    mid = uuid4()
    q = hub.subscribe(mid)
    assert mid in hub._channels
    hub.unsubscribe(mid, q)
    assert mid not in hub._channels


def test_queue_full_drops_oldest_keeps_newest_assert_order() -> None:
    # Publish messages 1..257 into a queue of maxsize 256.
    # Message 1 is the oldest; when 257 is pushed in, 1 is evicted.
    # Expected retained: messages 2..257 in order.
    hub = BroadcastHub()
    mid = uuid4()
    q = hub.subscribe(mid)
    for i in range(1, 258):  # 1, 2, …, 257
        hub.publish(mid, i)
    assert q.qsize() == 256
    items = [q.get_nowait() for _ in range(256)]
    assert items[0] == 2
    assert items[-1] == 257
    assert q.empty()


def test_slow_subscriber_overflow_does_not_affect_fast_subscriber() -> None:
    hub = BroadcastHub()
    mid = uuid4()
    slow_q = hub.subscribe(mid)
    fast_q = hub.subscribe(mid)
    # Fill the slow queue to capacity
    for i in range(256):
        slow_q.put_nowait(i)
    # Publish a new message — slow_q overflows, fast_q must still receive it
    hub.publish(mid, "important")
    assert fast_q.get_nowait() == "important"


def test_snapshot_iteration_does_not_raise_on_set_mutation() -> None:
    """publish() snapshots subscribers with tuple(); mutations between calls do not raise."""
    hub = BroadcastHub()
    mid = uuid4()
    q1 = hub.subscribe(mid)
    q2 = hub.subscribe(mid)
    hub.publish(mid, "first")
    hub.unsubscribe(mid, q1)  # mutate live set between publishes
    hub.publish(mid, "second")  # snapshot now only contains q2 — no RuntimeError
    assert q1.get_nowait() == "first"
    assert q2.get_nowait() == "first"
    assert q2.get_nowait() == "second"
    assert q1.empty()
