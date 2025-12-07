# Custom exceptions for ansari-whatsapp
"""Custom exception classes for the Ansari WhatsApp service."""


class AnsariClientError(Exception):
    """Base exception for Ansari client errors."""
    pass


class UserRegistrationError(AnsariClientError):
    """User registration failed."""
    pass


class UserExistsCheckError(AnsariClientError):
    """Checking if user exists failed."""
    pass


class ThreadCreationError(AnsariClientError):
    """Thread creation failed."""
    pass


class ThreadHistoryError(AnsariClientError):
    """Retrieving thread history failed."""
    pass


class ThreadInfoError(AnsariClientError):
    """Retrieving thread info failed."""
    pass


class MessageProcessingError(AnsariClientError):
    """Message processing failed."""
    pass
