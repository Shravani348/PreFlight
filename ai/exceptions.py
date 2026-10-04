"""Custom exceptions for the AI module."""


class AIProcessingError(Exception):
    """Base exception for all AI processing errors."""


class DocumentProcessingError(AIProcessingError):
    """Raised when document loading or preprocessing fails."""


class DocumentNotFoundError(DocumentProcessingError):
    """Raised when the specified document file does not exist."""


class UnsupportedDocumentError(DocumentProcessingError):
    """Raised when the document file format is unsupported."""


class CorruptedDocumentError(DocumentProcessingError):
    """Raised when the document is corrupt or cannot be opened/parsed."""


class ClassificationError(AIProcessingError):
    """Raised when document classification fails."""


class ExtractionError(AIProcessingError):
    """Raised when information extraction fails."""


class NormalizationError(AIProcessingError):
    """Raised when data normalization fails."""


class MatchingError(AIProcessingError):
    """Raised when cross-document matching fails."""


class InstructionError(AIProcessingError):
    """Raised when instruction parsing fails."""
