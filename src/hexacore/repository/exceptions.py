"""Repository-specific exception types."""


class PromiseNotReadyError(RuntimeError):
    """
    Exception raised when a promise is not ready.
    """


class NotFoundError(RuntimeError):
    """
    Exception raised when an object is not found.
    """
