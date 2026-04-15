from __future__ import annotations

from redis import Redis
from rq import Queue


def create_queue(redis_url: str, queue_name: str = "imports") -> Queue:
    connection = Redis.from_url(redis_url)
    return Queue(queue_name, connection=connection)
