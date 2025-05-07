class LoginError(Exception):
    """Raised when login fails, typically due to a missing token or bad response."""

    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception