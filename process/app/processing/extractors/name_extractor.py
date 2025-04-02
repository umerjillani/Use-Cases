"""
Intelligent Document Processing System
Name extraction
"""

import re
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Common name prefixes
NAME_PREFIXES = ['mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'rev', 'hon']

# Common name suffixes
NAME_SUFFIXES = ['jr', 'sr', 'ii', 'iii', 'iv', 'ph.d', 'md', 'esq']

# Name labels that might appear near names
NAME_LABELS = [
    'insured', 'insured name', 'name of insured', 'policyholder', 'claimant', 'claimant name',
    'mortgagee', 'agent', 'agent name', 'broker', 'broker name', 'payee', 'payor',
    'name', 'full name', 'customer', 'customer name', 'client', 'client name',
    'prepared by', 'approved by', 'submitted by', 'signed by', 'authorized by'
]

# Business entity indicators
BUSINESS_INDICATORS = [
    'inc', 'llc', 'ltd', 'corp', 'corporation', 'company', 'co', 'lp', 'llp',
    'incorporated', 'limited', 'partners', 'partnership', 'associates', 'group',
    'trust', 'agency', 'bank', 'services', 'solutions', 'enterprises', 'holdings',
    'property', 'properties', 'insurance', 'financial', 'management', 'investments'
]

def extract_names(text, name_type='person'):
    """
    Extract names from text
    
    Args:
        text: Text to extract names from
        name_type: Type of name to extract ('person' or 'business')
        
    Returns:
        str: Most likely extracted name or empty string if not found
    """
    try:
        # Check if text is None or empty
        if not text:
            return ""
        
        # Split text into lines
        lines = text.split('\n')
        
        names = []
        
        # Process each line
        for line in lines:
            # Look for names with labels
            for label in NAME_LABELS:
                # Look for label in line (case insensitive)
                label_match = re.search(r'{}[:\s]*(.+)'.format(re.escape(label)), line, re.IGNORECASE)
                if label_match:
                    name_text = label_match.group(1).strip()
                    
                    # Clean up the name text
                    name_text = clean_name(name_text)
                    
                    # Skip empty or too short names
                    if not name_text or len(name_text) < 3:
                        continue
                    
                    # Check if name matches requested type
                    if name_type == 'business' and is_business_name(name_text):
                        names.append({
                            'name': name_text,
                            'label': label,
                            'confidence': 0.9  # High confidence due to label
                        })
                    elif name_type == 'person' and not is_business_name(name_text):
                        names.append({
                            'name': name_text,
                            'label': label,
                            'confidence': 0.9  # High confidence due to label
                        })
            
            # Also look for names without labels
            if name_type == 'person':
                person_names = extract_person_names_from_line(line)
                for name in person_names:
                    # Skip if already found with a label
                    if not any(n['name'].lower() == name.lower() for n in names):
                        names.append({
                            'name': name,
                            'label': None,
                            'confidence': 0.7  # Lower confidence without label
                        })
            else:  # business
                business_names = extract_business_names_from_line(line)
                for name in business_names:
                    # Skip if already found with a label
                    if not any(n['name'].lower() == name.lower() for n in names):
                        names.append({
                            'name': name,
                            'label': None,
                            'confidence': 0.7  # Lower confidence without label
                        })
        
        # Return the highest confidence name
        if names:
            names.sort(key=lambda x: x['confidence'], reverse=True)
            return names[0]['name']
        
        return ""
    
    except Exception as e:
        logger.error(f"Error extracting names: {str(e)}", exc_info=True)
        return ""

def extract_person_names_from_line(line):
    """
    Extract potential person names from a line of text
    
    Args:
        line: Line of text
        
    Returns:
        list: List of extracted names
    """
    try:
        names = []
        
        # Look for names with prefixes
        prefix_pattern = r'\b(?:' + '|'.join(NAME_PREFIXES) + r')\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})'
        prefix_matches = re.finditer(prefix_pattern, line, re.IGNORECASE)
        for match in prefix_matches:
            name = match.group(1).strip()
            if name and len(name) > 3:
                names.append(name)
        
        # Look for capitalized names (2-3 words, each capitalized)
        name_pattern = r'\b([A-Z][a-z]+(?:[-\s]+[A-Z][a-z]+){1,2})'
        name_matches = re.finditer(name_pattern, line)
        for match in name_matches:
            name = match.group(1).strip()
            
            # Skip if name is too short or contains business indicators
            if name and len(name) > 3 and not is_business_name(name):
                names.append(name)
        
        # Look for names with suffixes
        suffix_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+(?:' + '|'.join(NAME_SUFFIXES) + r')\b'
        suffix_matches = re.finditer(suffix_pattern, line, re.IGNORECASE)
        for match in suffix_matches:
            name = match.group(1).strip()
            if name and len(name) > 3:
                names.append(name)
        
        return names
    
    except Exception as e:
        logger.error(f"Error extracting person names from line: {str(e)}", exc_info=True)
        return []

def extract_business_names_from_line(line):
    """
    Extract potential business names from a line of text
    
    Args:
        line: Line of text
        
    Returns:
        list: List of extracted business names
    """
    try:
        names = []
        
        # Look for business names with indicators
        for indicator in BUSINESS_INDICATORS:
            # Pattern for "Name Indicator" or "Name, Indicator"
            pattern = r'\b([A-Z][A-Za-z0-9\s&\'\-\.]{3,50})\s*(?:,\s*)?' + indicator + r'\b'
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip() + ' ' + indicator
                name = clean_name(name)
                if name and len(name) > 5:
                    names.append(name)
        
        # Look for capitalized multi-word entities that might be businesses
        # (more than 2 words, all or most capitalized)
        pattern = r'\b([A-Z][A-Za-z0-9\s&\'\-\.]{10,50})\b'
        matches = re.finditer(pattern, line)
        for match in matches:
            name = match.group(1).strip()
            name = clean_name(name)
            
            # Check if it has multiple capitalized words and contains business indicators
            words = name.split()
            if len(words) >= 2 and has_business_indicator(name) and not is_person_name(name):
                names.append(name)
        
        return names
    
    except Exception as e:
        logger.error(f"Error extracting business names from line: {str(e)}", exc_info=True)
        return []

def clean_name(name):
    """
    Clean up extracted name
    
    Args:
        name: Name to clean
        
    Returns:
        str: Cleaned name
    """
    # Remove trailing punctuation and extra spaces
    name = re.sub(r'[,;:."]$', '', name).strip()
    
    # Remove any trailing/leading special characters
    name = re.sub(r'^[^A-Za-z0-9]+|[^A-Za-z0-9]+$', '', name).strip()
    
    # Replace multiple spaces with a single space
    name = re.sub(r'\s+', ' ', name)
    
    return name

def is_business_name(name):
    """
    Check if name is likely a business name
    
    Args:
        name: Name to check
        
    Returns:
        bool: True if likely a business name, False otherwise
    """
    name_lower = name.lower()
    
    # Check for business indicators
    if has_business_indicator(name):
        return True
    
    # Check for person name indicators
    if is_person_name(name):
        return False
    
    # Look for other business-like characteristics
    if re.search(r'&', name):
        return True
    
    if len(name.split()) > 3:
        # Longer names are more likely to be businesses
        return True
    
    return False

def has_business_indicator(name):
    """
    Check if name contains business indicators
    
    Args:
        name: Name to check
        
    Returns:
        bool: True if name contains business indicators, False otherwise
    """
    name_lower = name.lower()
    
    # Check for common business entity types
    for indicator in BUSINESS_INDICATORS:
        if re.search(r'\b' + re.escape(indicator) + r'\b', name_lower):
            return True
    
    return False

def is_person_name(name):
    """
    Check if name is likely a person name
    
    Args:
        name: Name to check
        
    Returns:
        bool: True if likely a person name, False otherwise
    """
    words = name.split()
    
    # Check for prefix
    if len(words) > 1 and words[0].lower().replace('.', '') in NAME_PREFIXES:
        return True
    
    # Check for suffix
    if len(words) > 1 and words[-1].lower().replace('.', '') in NAME_SUFFIXES:
        return True
    
    # Look for typical person name pattern (1-3 words, each capitalized)
    if 1 <= len(words) <= 3 and all(word[0].isupper() for word in words if word):
        return True
    
    return False

def extract_all_names(text):
    """
    Extract all names from text (both person and business)
    
    Args:
        text: Text to extract names from
        
    Returns:
        dict: Dictionary with person and business names
    """
    return {
        'person': extract_names(text, 'person'),
        'business': extract_names(text, 'business')
    }