from __future__ import annotations

"""Queue helpers for dispatching background import jobs."""

import logging
import os
from threading import Thread
from typing import Any, Callable

from redis import Redis


logger = logging.getLogger(__name__)


class LocalThreadQueue:
    """Tiny development queue for platforms where RQ workers are unavailable."""

    def enqueue(
        self,
        function: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Thread:
        """Run a queued job in a daemon thread and return the thread handle."""

        kwargs.pop("job_timeout", None)
        thread = Thread(target=self._run_job, args=(function, args, kwargs), daemon=True)
        thread.start()
        return thread

    @staticmethod
    def _run_job(
        function: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        try:
            function(*args, **kwargs)
        except Exception:
            logger.exception("Local background job failed.")


# Queue creation is factored out mainly to keep startup code declarative and to
# give the queue boundary a single place to evolve if infrastructure changes.
def create_queue(
    redis_url: str,
    queue_name: str = "imports",
    *,
    use_local_thread_queue: bool = False,
) -> Any:
    """Create a background queue for import jobs."""

    if use_local_thread_queue:
        return LocalThreadQueue()

    from rq import Queue

    connection = Redis.from_url(redis_url)
    return Queue(queue_name, connection=connection)


def should_use_local_thread_queue(environment: str) -> bool:
    """Use the in-process queue for Windows development runs."""

    return environment == "development" and os.name == "nt"
