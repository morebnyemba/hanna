# whatsappcrm_backend/realtime.py
"""
Helpers for pushing Channels group messages from synchronous code.

The messaging and flow Celery workers run on the gevent pool, where every
greenlet shares a single OS thread. ``async_to_sync`` spins up an event loop in
that thread and, while it waits on Redis, gevent switches to another greenlet --
which then finds a loop already running in "its" thread and raises:

    RuntimeError: You cannot use AsyncToSync in the same thread as an async
    event loop - just await the async function directly.

Serialising the calls gives each greenlet the thread's event loop to itself.
Under gevent the lock is monkey-patched, so waiting on it yields to the hub
rather than blocking the thread; under prefork/daphne it is an ordinary lock and
the contention is negligible.

A broadcast is a live-UI nicety, never a reason to fail the task or the ORM save
that triggered it, so failures are logged and swallowed.
"""
import logging
import threading

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

# Created at import time, which is always after the gevent pool has monkey-patched
# threading -- Celery patches before Django is set up, and this module is only
# imported from Django apps.
_broadcast_lock = threading.Lock()

# A group_send is a couple of Redis round trips. Waiting anywhere near this long
# means something is wedged, and dropping an update beats stalling the worker.
_LOCK_TIMEOUT_SECONDS = 5.0


def group_send(group_name, message):
    """
    Send ``message`` to the channel layer group ``group_name``.

    Returns True if the message was handed to the channel layer, False if it was
    dropped (no channel layer, lock timeout, or a transport error).
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning("Cannot broadcast to '%s': no channel layer configured.", group_name)
        return False

    if not _broadcast_lock.acquire(timeout=_LOCK_TIMEOUT_SECONDS):
        logger.warning(
            "Dropped broadcast to '%s': timed out waiting for the broadcast lock.", group_name
        )
        return False

    try:
        async_to_sync(channel_layer.group_send)(group_name, message)
        return True
    except Exception:
        logger.warning("Failed to broadcast to group '%s'.", group_name, exc_info=True)
        return False
    finally:
        _broadcast_lock.release()
