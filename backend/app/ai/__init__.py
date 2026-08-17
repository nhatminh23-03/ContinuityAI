"""AI layer. Model access lives behind `AIProvider` and nowhere else."""

from .provider import AIProvider, ExtractionContext, get_provider
from .validation import ValidationOutcome, validate_extraction

__all__ = [
    "AIProvider",
    "ExtractionContext",
    "ValidationOutcome",
    "get_provider",
    "validate_extraction",
]
