import time
from collections import defaultdict, deque
from threading import Lock
from typing import Generator

from .base_event_listener import BaseEventListener


class FakeEventListener(BaseEventListener):
    """
    A fake event listener for testing purposes.
    """

    def __init__(self, poll_interval: float = 0.1):
        """
        Initialize the FakeEventListener.

        Args:
            poll_interval (float): Time in seconds to wait between polling attempts
                when no messages are available. Defaults to 0.1.
        """
        self.queue_to_messages = defaultdict(deque)
        self._lock = Lock()
        self._poll_interval = poll_interval
        self._stopped = False

    def push_in_queue(self, queue_name: str, message: dict):
        """
        Push a message into a queue.

        Args:
            queue_name (str): The name of the queue to push the message to.
            message (dict): The message to push.
        """
        with self._lock:
            self.queue_to_messages[queue_name].append(message)

    def listen(self, queue_name: str) -> Generator[dict, None, None]:
        """
        Listen to a queue and yield messages.

        Args:
            queue_name (str): The name of the queue to listen to.

        Yields:
            Generator[dict, None, None]: A generator of messages.
        """
        while not self._stopped:
            message = None
            with self._lock:
                if self.queue_to_messages[queue_name]:
                    message = self.queue_to_messages[queue_name].popleft()

            if message is not None:
                yield message
            else:
                time.sleep(self._poll_interval)

    def stop(self):
        """Stop the listener gracefully."""
        self._stopped = True

    def open(self):
        """Open the listener. For the fake listener, this is a no-op."""
        pass

    def close(self):
        self.stop()
