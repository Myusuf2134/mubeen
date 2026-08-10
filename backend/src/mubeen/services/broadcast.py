"""In-process pub/sub hub: one asyncio.Queue per subscriber, keyed by masjid_id.

Single-process in-memory design. This is the Redis pub/sub swap-in point for
multi-replica scaling (MB-022). Until then, the backend must run exactly one
Uvicorn worker and one ECS Fargate replica — multiple workers silently break
cross-client fan-out because each process has its own hub instance.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import structlog

log = structlog.get_logger()


class BroadcastHub:
    """Channel-per-masjid fan-out hub.

    All methods are synchronous — they contain no blocking I/O, so keeping them
    sync makes it impossible to accidentally yield mid-mutation of the subscriber
    set and simplifies callers.
    """

    def __init__(self) -> None:
        self._channels: dict[UUID, set[asyncio.Queue]] = {}

    def subscribe(self, masjid_id: UUID) -> asyncio.Queue:
        """Register a new subscriber for masjid_id. Returns the subscriber's queue."""
        if masjid_id not in self._channels:
            self._channels[masjid_id] = set()
        q: asyncio.Queue = asyncio.Queue(maxsize=256)
        self._channels[masjid_id].add(q)
        return q

    def unsubscribe(self, masjid_id: UUID, queue: asyncio.Queue) -> None:
        """Remove a subscriber's queue. Idempotent; unknown queue or channel does not raise.

        After the final subscriber leaves, the masjid key is deleted so abandoned
        channel entries never accumulate.
        """
        channel = self._channels.get(masjid_id)
        if channel is None:
            return
        channel.discard(queue)
        if not channel:
            del self._channels[masjid_id]

    def publish(self, masjid_id: UUID, message: object) -> None:
        """Fan out message to all subscribers on masjid_id. Non-blocking.

        Iterates over a STABLE SNAPSHOT so a concurrent disconnect cannot cause
        "set changed size during iteration". On a full queue, the oldest item is
        dropped and the newest is enqueued (recent captions matter more than delayed
        ones during a live khutbah).
        """
        for queue in tuple(self._channels.get(masjid_id, ())):
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                log.warning("queue_overflow_dropped", masjid_id=str(masjid_id))
                try:
                    queue.get_nowait()  # drop oldest
                except asyncio.QueueEmpty:
                    pass
                try:
                    queue.put_nowait(message)
                except asyncio.QueueFull:
                    pass  # stays non-blocking no matter what

    def subscriber_count(self, masjid_id: UUID) -> int:
        """Return the number of active subscribers on masjid_id."""
        return len(self._channels.get(masjid_id, ()))


# Process-wide singleton.
hub = BroadcastHub()
