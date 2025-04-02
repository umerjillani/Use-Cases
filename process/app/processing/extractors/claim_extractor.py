"""
Intelligent Document Processing System
Claim number extraction
"""

import re
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Common claim number patterns
CLAIM_PATTERNS = [
    # Basic claim number patterns
    r'(?:claim|case)(?:\s+(?:no|number|#))?\s*[:;]?\s*([A-Z0-9]{5,15})',
    r'(?:claim|case)(?:\s+(?:no|number|#))?\s*[:;]?\s*([A-Z0-9]{2,7}[-\s][A-Z0-9]{2,7})',
    
    # Variations with additional segments
    r'(?:claim|case)(?:\s+(?:no|number|#))?\s*[:;]?\s*([A-Z0-9]{2,5}[-\s][A-Z0-9]{2,5}[-\s][A-Z0-9]{2,5})',
    
    # Reference or Claim ID formats
    r'(?:claim\s+(?:id|reference|ref))[:;]?\s*([A-Z0-9]{5,15})',
    r'(?:claim\s+(?:id|reference|ref))[:;]?\s*([A-Z0-9]{2,7}[-\s][A-Z0-9]{2,7})',
    
    # Insurance-specific formats
    r'(?:insurance\s+claim)(?:\s+(?:no|number|#))?\s*[:;]?\s*([A-Z0-9]{5,15})',
    r'(?:loss\s+(?:no|number))[:;]?\s*([A-Z0-9]{5,15})',
]

# Terms that might indicate the start of a line containing a claim number
CLAIM_LINE_STARTERS = [
    'claim', 'case', 'incident', 'loss', 'reference', 'ref', 'number', 'no', '#'
]

def extract_claim_number(text):
    """
    Extract claim number from text
    
    Args:
        text: Text to extract claim number from
        
    Returns:
        str: Extracted claim number or empty string if not found
    """
    try:
        # Check if text is None or empty
        if not text:
            return ""
        
        # Try different patterns
        for pattern in CLAIM_PATTERNS:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                claim_number = matches.group(1).strip()
                
                # Validate the claim number format
                if validate_claim_number(claim_number):
                    return clean_claim_number(claim_number)
        
        # If no match found with standard patterns, try line-by-line analysis
        lines = text.split('\n')
        for line in lines:
            # Look for lines that likely contain a claim number
            line_lower = line.lower()
            if any(starter in line_lower for starter in CLAIM_LINE_STARTERS):
                # Try to extract alphanumeric string that could be a claim number
                potential_numbers = re.findall(r'[A-Z0-9]{5,15}', line)
                for number in potential_numbers:
                    if validate_claim_number(number):
                        return clean_claim_number(number)
                
                # Try with hyphens or spaces
                potential_numbers = re.findall(r'[A-Z0-9]{2,7}[-\s][A-Z0-9]{2,7}', line)
                for number in potential_numbers:
                    # Remove spaces and validate
                    clean_number = number.replace(' ', '').replace('-', '')
                    if validate_claim_number(clean_number):
                        return clean_claim_number(number)
        
        # If nothing found, return empty string
        return ""
    
    except Exception as e:
        logger.error(f"Error extracting claim number: {str(e)}", exc_info=True)
        return ""

def validate_claim_number(claim_number):
    """
    Validate claim number format
    
    Args:
        claim_number: Claim number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Remove spaces, hyphens, and other separators
    clean_number = claim_number.replace(' ', '').replace('-', '').replace('/', '').replace('_', '')
    
    # Simple validation - claim numbers should be alphanumeric
    # and have a minimum length
    if not clean_number.isalnum():
        return False
    
    # Check minimum length (customize based on your claim number format)
    if len(clean_number) < 5:
        return False
    
    # Check if it contains at least one number
    if not any(c.isdigit() for c in clean_number):
        return False
    
    # Additional validation rules can be added here based on specific claim number formats
    
    return True

def clean_claim_number(claim_number):
    """
    Clean and normalize claim number
    
    Args:
        claim_number: Claim number to clean
        
    Returns:
        str: Cleaned claim number
    """
    # Convert to uppercase
    claim_number = claim_number.upper()
    
    # Normalize separators (use hyphen consistently)
    claim_number = claim_number.replace(' ', '-').replace('/', '-').replace('_', '-')
    
    # Remove duplicate separators
    claim_number = re.sub(r'-+', '-', claim_number)
    
    # Remove leading/trailing separators
    claim_number = claim_number.strip('-')
    
    return claim_number

def extract_claim_details(text):
    """
    Extract comprehensive claim details
    
    Args:
        text: Text to extract claim details from
        
    Returns:
        dict: Dictionary of claim details
    """
    try:
        details = {}
        
        # Extract claim number
        details['claim_number'] = extract_claim_number(text)
        
        # Extract claim type
        details['claim_type'] = extract_claim_type(text)
        
        # Extract claim status (if present)
        details['claim_status'] = extract_claim_status(text)
        
        # Extract loss date (if present)
        from app.processing.extractors.date_extractor import extract_dates
        dates = extract_dates(text)
        
        # Look for loss date specifically
        loss_date = None
        for date in dates:
            if date.get('label') and 'loss' in date.get('label').lower():
                loss_date = date.get('date')
                break
        
        details['loss_date'] = loss_date
        
        return details
    
    except Exception as e:
        logger.error(f"Error extracting claim details: {str(e)}", exc_info=True)
        return {'claim_number': ''}

def extract_claim_type(text):
    """
    Extract claim type from text
    
    Args:
        text: Text to extract claim type from
        
    Returns:
        str: Extracted claim type or None if not found
    """
    try:
        # Common claim types
        claim_types = {
            'auto': ['auto', 'vehicle', 'car', 'collision', 'automobile'],
            'property': ['property', 'home', 'house', 'building', 'dwelling', 'fire'],
            'liability': ['liability', 'general liability', 'personal liability'],
            'medical': ['medical', 'health', 'injury', 'bodily injury'],
            'workers_comp': ['workers', 'compensation', 'worker', 'workplace']
        }
        
        text_lower = text.lower()
        
        # Check for claim type indicators
        for claim_type, keywords in claim_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Look for the keyword in context of claim type
                    if re.search(r'claim\s+type\s*[:;]?\s*' + keyword, text_lower) or \
                       re.search(r'type\s+of\s+claim\s*[:;]?\s*' + keyword, text_lower) or \
                       re.search(keyword + r'\s+claim', text_lower):
                        return claim_type
        
        # If no specific type found
        return None
    
    except Exception as e:
        logger.error(f"Error extracting claim type: {str(e)}", exc_info=True)
        return None

def extract_claim_status(text):
    """
    Extract claim status from text
    
    Args:
        text: Text to extract claim status from
        
    Returns:
        str: Extracted claim status or None if not found
    """
    try:
        # Common claim statuses
        status_patterns = [
            (r'claim\s+status\s*[:;]?\s*([A-Za-z\s]+)', 1),
            (r'status\s*[:;]?\s*([A-Za-z\s]+)', 1),
            (r'claim\s+is\s+([A-Za-z\s]+)', 1)
        ]
        
        for pattern, group in status_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                status = match.group(group).strip().lower()
                
                # Normalize status
                if 'open' in status:
                    return 'open'
                elif 'closed' in status or 'complete' in status or 'resolved' in status:
                    return 'closed'
                elif 'pending' in status or 'process' in status or 'review' in status:
                    return 'pending'
                elif 'denied' in status or 'reject' in status:
                    return 'denied'
                else:
                    return status
        
        return None
    
    except Exception as e:
        logger.error(f"Error extracting claim status: {str(e)}", exc_info=True)
        return None