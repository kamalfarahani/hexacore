class FailedToListenError(Exception):
    """
    Exception raised by RabbitMQEventListener.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
