"""
Intelligent Document Processing System
Document classifier
"""

import re
import logging
from collections import Counter

# Configure logging
logger = logging.getLogger(__name__)

# Document type keyword patterns
DOCUMENT_PATTERNS = {
    'claim': [
        r'claim\s+(?:form|report|notice)',
        r'notice\s+of\s+(?:claim|loss)',
        r'insurance\s+claim',
        r'claim\s+number',
        r'claimant',
        r'date\s+of\s+(?:loss|incident|claim)',
        r'damage\s+report',
        r'incident\s+report',
        r'loss\s+report'
    ],
    'agency_services': [
        r'agent\s+(?:services|request)',
        r'agency\s+(?:services|request)',
        r'service\s+request',
        r'insurance\s+(?:agent|agency)',
        r'broker\s+services',
        r'agent\s+change',
        r'commission'
    ],
    'cancellation': [
        r'(?:policy|insurance)\s+cancellation',
        r'cancel(?:led|lation)',
        r'notice\s+of\s+cancellation',
        r'terminate\s+(?:policy|insurance|coverage)',
        r'termination\s+(?:form|notice)',
        r'policy\s+termination'
    ],
    'mortgage_change': [
        r'mortgage\s+(?:change|update)',
        r'mortgagee\s+(?:change|update)',
        r'loan\s+(?:number|#)',
        r'lender\s+(?:change|update)',
        r'change\s+(?:of|in)\s+mortgage',
        r'mortgage\s+clause',
        r'mortgage\s+(?:company|lender|provider)'
    ],
    'payment': [
        r'payment\s+(?:form|receipt|confirmation)',
        r'premium\s+payment',
        r'payment\s+(?:of|for)\s+premium',
        r'check\s+(?:enclosed|payment)',
        r'credit\s+card\s+payment',
        r'receipt',
        r'invoice\s+payment'
    ]
}

# Document type keywords
DOCUMENT_KEYWORDS = {
    'claim': ['claim', 'loss', 'damage', 'incident', 'claimant', 'insured', 'coverage'],
    'agency_services': ['agent', 'agency', 'service', 'broker', 'commission', 'producer'],
    'cancellation': ['cancel', 'terminate', 'end', 'stop', 'withdrawal', 'discontinue'],
    'mortgage_change': ['mortgage', 'mortgagee', 'lender', 'loan', 'bank', 'finance', 'property'],
    'payment': ['payment', 'premium', 'pay', 'check', 'invoice', 'receipt', 'amount']
}

def classify_document(text):
    """
    Classify document based on text content
    
    Args:
        text: Document text
        
    Returns:
        str: Document type (claim, agency_services, cancellation, mortgage_change, payment)
    """
    try:
        # Check if text is None or empty
        if not text:
            return 'unknown'
        
        # Convert text to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Pattern matching approach
        pattern_scores = {}
        for doc_type, patterns in DOCUMENT_PATTERNS.items():
            pattern_scores[doc_type] = 0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    pattern_scores[doc_type] += 1
        
        # Keyword frequency approach
        keyword_scores = {}
        for doc_type, keywords in DOCUMENT_KEYWORDS.items():
            keyword_scores[doc_type] = 0
            for keyword in keywords:
                keyword_scores[doc_type] += text_lower.count(keyword)
        
        # Combine scores with weights
        # Pattern matches are more reliable (higher weight)
        combined_scores = {}
        for doc_type in DOCUMENT_PATTERNS.keys():
            combined_scores[doc_type] = (pattern_scores[doc_type] * 3) + keyword_scores[doc_type]
        
        # Get document type with highest score
        if combined_scores:
            max_score = max(combined_scores.values())
            
            # If max score is 0, document type is unknown
            if max_score == 0:
                return 'unknown'
            
            # Get all document types with max score
            max_types = [doc_type for doc_type, score in combined_scores.items() if score == max_score]
            
            # If multiple document types have the same score, use additional heuristics
            if len(max_types) > 1:
                return resolve_tie(text_lower, max_types)
            
            return max_types[0]
        
        return 'unknown'
    
    except Exception as e:
        logger.error(f"Error classifying document: {str(e)}", exc_info=True)
        return 'unknown'

def resolve_tie(text, document_types):
    """
    Resolve tie between document types
    
    Args:
        text: Document text
        document_types: List of tied document types
        
    Returns:
        str: Resolved document type
    """
    # Check for specific indicators
    if 'claim' in document_types:
        # Strong claim indicators
        if re.search(r'claim\s+number', text) or re.search(r'loss\s+date', text):
            return 'claim'
    
    if 'payment' in document_types:
        # Strong payment indicators
        if re.search(r'check\s+(?:number|#)', text) or re.search(r'payment\s+confirmation', text):
            return 'payment'
    
    if 'mortgage_change' in document_types:
        # Strong mortgage indicators
        if re.search(r'mortgage\s+clause', text) or re.search(r'loan\s+(?:number|#)', text):
            return 'mortgage_change'
    
    if 'cancellation' in document_types:
        # Strong cancellation indicators
        if re.search(r'cancel\s+(?:policy|insurance)', text) or re.search(r'cancellation\s+date', text):
            return 'cancellation'
    
    if 'agency_services' in document_types:
        # Strong agency indicators
        if re.search(r'agent\s+(?:code|number)', text) or re.search(r'broker\s+(?:code|number)', text):
            return 'agency_services'
    
    # Fall back to first type in list
    return document_types[0]

def get_confidence_score(text, doc_type):
    """
    Get confidence score for document classification
    
    Args:
        text: Document text
        doc_type: Document type
        
    Returns:
        float: Confidence score (0.0 - 1.0)
    """
    try:
        # Check if text is None or empty
        if not text or doc_type == 'unknown':
            return 0.0
        
        text_lower = text.lower()
        
        # Count pattern matches
        pattern_matches = 0
        total_patterns = len(DOCUMENT_PATTERNS[doc_type])
        
        for pattern in DOCUMENT_PATTERNS[doc_type]:
            if re.search(pattern, text_lower):
                pattern_matches += 1
        
        # Count keyword matches
        keyword_matches = 0
        total_keywords = len(DOCUMENT_KEYWORDS[doc_type])
        
        for keyword in DOCUMENT_KEYWORDS[doc_type]:
            if keyword in text_lower:
                keyword_matches += 1
        
        # Calculate confidence score
        # Patterns are weighted more heavily
        pattern_weight = 0.7
        keyword_weight = 0.3
        
        pattern_score = pattern_matches / total_patterns if total_patterns > 0 else 0
        keyword_score = keyword_matches / total_keywords if total_keywords > 0 else 0
        
        confidence = (pattern_score * pattern_weight) + (keyword_score * keyword_weight)
        
        return min(1.0, confidence)
    
    except Exception as e:
        logger.error(f"Error calculating confidence score: {str(e)}", exc_info=True)
        return 0.0