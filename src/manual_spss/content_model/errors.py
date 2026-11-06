"""Domain exceptions for loading and querying manual content."""


class ContentError(Exception):
    """Base class for errors surfaced by the content model."""


class ContentNotFoundError(ContentError):
    """Raised when a requested manual section does not exist."""


class ContentValidationError(ContentError, ValueError):
    """Raised when a manifest or content model violates its contract."""
