"""
Intelligent Document Processing System
Classifiers module initialization
"""

from app.processing.classifiers.document_classifier import (
    classify_document,
    resolve_tie,
    get_confidence_score,
    DOCUMENT_PATTERNS,
    DOCUMENT_KEYWORDS
)

# Export classifier functions
__all__ = [
    'classify_document',
    'resolve_tie',
    'get_confidence_score',
    'DOCUMENT_PATTERNS',
    'DOCUMENT_KEYWORDS'
]