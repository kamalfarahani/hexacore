"""Broker connection exception types."""


class OpenError(Exception):
    """Raised when the connection is not open or is already open."""


class ConsumeError(Exception):
    """Exception raised when there is an error consuming from a queue."""


class PublishError(Exception):
    """Exception raised when there is an error publishing to an exchange."""
