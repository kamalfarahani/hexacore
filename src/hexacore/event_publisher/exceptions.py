class FailedToPublishEventError(Exception):
    """
    Failed to publish event.
    """

    def __init__(self, message: str):
        """
        Initialize the exception.

        Args:
            message (str): The error message.
        """
        self.message = message
        super().__init__(self.message)
