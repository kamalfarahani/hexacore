"""Repository-specific exception types."""


class UnsupportedCommandError(TypeError):
    """Raised when a repository cannot execute a command type."""
