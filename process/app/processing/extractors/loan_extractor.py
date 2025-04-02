"""
Intelligent Document Processing System
Loan number extraction
"""

import re
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Common loan number patterns
LOAN_PATTERNS = [
    # Basic loan number patterns
    r'(?:loan|mortgage)(?:\s+(?:no|number|#))?\s*[:;]?\s*([A-Z0-9]{5,15})',
    r'(?:loan|mortgage)(?:\s+(?:no|number|#))?\s*[:;]?\s*([A-Z0-9]{3,7}[-\s][A-Z0-9]{3,7})',
    
    # Variations with additional segments
    r'(?:loan|mortgage)(?:\s+(?:no|number|#))?\s*[:;]?\s*([A-Z0-9]{2,5}[-\s][A-Z0-9]{2,5}[-\s][A-Z0-9]{2,5})',
    
    # Account number patterns that might be loan numbers
    r'(?:account)(?:\s+(?:no|number|#))?\s*[:;]?\s*([A-Z0-9]{5,15})',
    
    # Specific mortgage patterns
    r'(?:mortgage\s+(?:id|reference|ref))[:;]?\s*([A-Z0-9]{5,15})',
    r'(?:mortgage\s+(?:id|reference|ref))[:;]?\s*([A-Z0-9]{2,7}[-\s][A-Z0-9]{2,7})',
    
    # FHA/VA/USDA loan number patterns
    r'(?:fha|va|usda)\s+(?:no|number|#)\s*[:;]?\s*([A-Z0-9]{5,15})',
]

# Terms that might indicate the start of a line containing a loan number
LOAN_LINE_STARTERS = [
    'loan', 'mortgage', 'account', 'fha', 'va', 'usda', 'lender', 'reference', 'ref', 'number', 'no', '#'
]

def extract_loan_number(text):
    """
    Extract loan number from text
    
    Args:
        text: Text to extract loan number from
        
    Returns:
        str: Extracted loan number or empty string if not found
    """
    try:
        # Check if text is None or empty
        if not text:
            return ""
        
        # Try different patterns
        for pattern in LOAN_PATTERNS:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                loan_number = matches.group(1).strip()
                
                # Validate the loan number format
                if validate_loan_number(loan_number):
                    return clean_loan_number(loan_number)
        
        # If no match found with standard patterns, try line-by-line analysis
        lines = text.split('\n')
        for line in lines:
            # Look for lines that likely contain a loan number
            line_lower = line.lower()
            if any(starter in line_lower for starter in LOAN_LINE_STARTERS):
                # Try to extract alphanumeric string that could be a loan number
                potential_numbers = re.findall(r'[A-Z0-9]{5,15}', line)
                for number in potential_numbers:
                    if validate_loan_number(number):
                        return clean_loan_number(number)
                
                # Try with hyphens or spaces
                potential_numbers = re.findall(r'[A-Z0-9]{2,7}[-\s][A-Z0-9]{2,7}', line)
                for number in potential_numbers:
                    # Remove spaces and validate
                    clean_number = number.replace(' ', '').replace('-', '')
                    if validate_loan_number(clean_number):
                        return clean_loan_number(number)
        
        # If nothing found, return empty string
        return ""
    
    except Exception as e:
        logger.error(f"Error extracting loan number: {str(e)}", exc_info=True)
        return ""

def validate_loan_number(loan_number):
    """
    Validate loan number format
    
    Args:
        loan_number: Loan number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Remove spaces, hyphens, and other separators
    clean_number = loan_number.replace(' ', '').replace('-', '').replace('/', '').replace('_', '')
    
    # Simple validation - loan numbers should be alphanumeric
    # and have a minimum length
    if not clean_number.isalnum():
        return False
    
    # Check minimum length (customize based on your loan number format)
    if len(clean_number) < 5:
        return False
    
    # Check if it contains at least one number
    if not any(c.isdigit() for c in clean_number):
        return False
    
    # Additional validation rules can be added here based on specific loan number formats
    
    return True

def clean_loan_number(loan_number):
    """
    Clean and normalize loan number
    
    Args:
        loan_number: Loan number to clean
        
    Returns:
        str: Cleaned loan number
    """
    # Convert to uppercase
    loan_number = loan_number.upper()
    
    # Normalize separators (use hyphen consistently)
    loan_number = loan_number.replace(' ', '-').replace('/', '-').replace('_', '-')
    
    # Remove duplicate separators
    loan_number = re.sub(r'-+', '-', loan_number)
    
    # Remove leading/trailing separators
    loan_number = loan_number.strip('-')
    
    return loan_number

def extract_loan_details(text):
    """
    Extract comprehensive loan details
    
    Args:
        text: Text to extract loan details from
        
    Returns:
        dict: Dictionary of loan details
    """
    try:
        details = {}
        
        # Extract loan number
        details['loan_number'] = extract_loan_number(text)
        
        # Extract loan type
        details['loan_type'] = extract_loan_type(text)
        
        # Extract loan amount (if present)
        from app.processing.extractors.amount_extractor import extract_amount
        details['loan_amount'] = extract_amount(text)
        
        # Extract lender name (if present)
        from app.processing.extractors.name_extractor import extract_names
        details['lender_name'] = extract_names(text, name_type='business')
        
        # Extract property address
        details['property_address'] = extract_property_address(text)
        
        return details
    
    except Exception as e:
        logger.error(f"Error extracting loan details: {str(e)}", exc_info=True)
        return {'loan_number': ''}

def extract_loan_type(text):
    """
    Extract loan type from text
    
    Args:
        text: Text to extract loan type from
        
    Returns:
        str: Extracted loan type or None if not found
    """
    try:
        # Common loan types
        loan_types = {
            'conventional': ['conventional'],
            'fha': ['fha', 'federal housing administration'],
            'va': ['va', 'veterans affairs', 'veteran'],
            'usda': ['usda', 'rural development', 'rural housing'],
            'jumbo': ['jumbo'],
            'arm': ['adjustable', 'arm', 'variable rate'],
            'fixed': ['fixed rate', 'fixed-rate', '30-year fixed', '15-year fixed'],
            'heloc': ['heloc', 'home equity line', 'equity line'],
            'home_equity': ['home equity', 'equity loan']
        }
        
        text_lower = text.lower()
        
        # Check for loan type indicators
        for loan_type, keywords in loan_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Look for the keyword in context of loan type
                    if re.search(r'loan\s+type\s*[:;]?\s*' + keyword, text_lower) or \
                       re.search(r'type\s+of\s+loan\s*[:;]?\s*' + keyword, text_lower) or \
                       re.search(keyword + r'\s+loan', text_lower) or \
                       re.search(keyword + r'\s+mortgage', text_lower):
                        return loan_type
        
        # If no specific type found
        return None
    
    except Exception as e:
        logger.error(f"Error extracting loan type: {str(e)}", exc_info=True)
        return None

def extract_property_address(text):
    """
    Extract property address from text
    
    Args:
        text: Text to extract property address from
        
    Returns:
        str: Extracted property address or empty string if not found
    """
    try:
        # Look for property address indicators
        address_patterns = [
            r'property\s+address\s*[:;]?\s*([^\n]{5,100})',
            r'subject\s+property\s*[:;]?\s*([^\n]{5,100})',
            r'property\s+location\s*[:;]?\s*([^\n]{5,100})',
            r'premises\s+address\s*[:;]?\s*([^\n]{5,100})',
            r'mortgaged\s+property\s*[:;]?\s*([^\n]{5,100})'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                address = match.group(1).strip()
                # Clean up address
                address = re.sub(r'\s+', ' ', address)  # Normalize spaces
                address = re.sub(r'[,;]\s*$', '', address)  # Remove trailing commas/semicolons
                return address
        
        # If no match found with standard patterns, look for standalone address patterns
        lines = text.split('\n')
        for line in lines:
            # Basic US address pattern: street number, street name, optional apartment, city, state zip
            if re.match(r'\d+\s+[A-Za-z0-9\s\.,]+,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}(-\d{4})?', line):
                return line.strip()
        
        return ""
    
    except Exception as e:
        logger.error(f"Error extracting property address: {str(e)}", exc_info=True)
        return ""