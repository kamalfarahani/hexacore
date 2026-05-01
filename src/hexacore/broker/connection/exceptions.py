class OpenError(Exception):
    """Exception raised when connection is not open"""


class ConsumeError(Exception):
    """Exception raised when there is an error consuming from a queue."""


class PublishError(Exception):
    """Exception raised when there is an error publishing to an exchange."""
