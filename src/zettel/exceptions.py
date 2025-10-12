"""Custom exceptions for the Zettelkasten tool."""

class ZettelkastenError(Exception):
    """Base exception for all errors in this application."""
    pass

class FileNotFoundError(ZettelkastenError):
    """Raised when an expected file is not found."""
    pass

class APIConnectionError(ZettelkastenError):
    """Raised when there's an issue connecting to the AI API."""
    pass

class JSONParsingError(ZettelkastenError):
    """Raised when the AI API returns malformed JSON."""
    pass