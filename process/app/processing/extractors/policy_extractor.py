"""
Intelligent Document Processing System
Policy number extraction
"""

import re
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Common policy number patterns
POLICY_PATTERNS = [
    r'Policy\s*(?:#|No|Number|ID)?\s*[:;]?\s*([A-Z0-9]{8,15})',
    r'Policy\s*(?:#|No|Number|ID)?\s*[:;]?\s*([A-Z0-9]{3,7}[-\s][A-Z0-9]{3,7})',
    r'(?:Policy|Insurance)\s*(?:ID|Number|No)?\s*[:;]?\s*([A-Z0-9]{2,5}[-\s][A-Z0-9]{5,10})',
    r'(?<!Claim\s)(?<!Loan\s)(?<!Reference\s)Number\s*[:;]?\s*([A-Z0-9]{8,15})',
]

def extract_policy_number(text):
    """
    Extract policy number from text
    
    Args:
        text: Text to extract policy number from
        
    Returns:
        str: Extracted policy number or empty string if not found
    """
    try:
        # Check if text is None or empty
        if not text:
            return ""
        
        # Try different patterns
        for pattern in POLICY_PATTERNS:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                policy_number = matches.group(1).strip()
                
                # Validate the policy number format
                if validate_policy_number(policy_number):
                    return policy_number
        
        # Try more general approach - look for lines with "policy" word
        lines = text.split('\n')
        for line in lines:
            if 'policy' in line.lower():
                # Try to extract alphanumeric string that could be a policy number
                potential_numbers = re.findall(r'[A-Z0-9]{8,15}', line)
                for number in potential_numbers:
                    if validate_policy_number(number):
                        return number
                
                # Try with hyphens or spaces
                potential_numbers = re.findall(r'[A-Z0-9]{3,7}[-\s][A-Z0-9]{3,7}', line)
                for number in potential_numbers:
                    # Remove spaces and validate
                    clean_number = number.replace(' ', '').replace('-', '')
                    if validate_policy_number(clean_number):
                        return clean_number
        
        # If nothing found, return empty string
        return ""
    
    except Exception as e:
        logger.error(f"Error extracting policy number: {str(e)}", exc_info=True)
        return ""

def validate_policy_number(policy_number):
    """
    Validate policy number format
    
    Args:
        policy_number: Policy number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Remove spaces and hyphens
    clean_number = policy_number.replace(' ', '').replace('-', '')
    
    # Simple validation - policy numbers should be alphanumeric
    # and have a minimum length
    if not clean_number.isalnum():
        return False
    
    # Check minimum length (customize based on your policy number format)
    if len(clean_number) < 6:
        return False
    
    # Additional validation rules can be added here based on specific policy number formats
    
    return True

def extract_policy_numbers(text):
    """
    Extract all potential policy numbers from text
    
    Args:
        text: Text to extract policy numbers from
        
    Returns:
        list: List of extracted policy numbers
    """
    policy_numbers = []
    
    try:
        # Try different patterns
        for pattern in POLICY_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                policy_number = match.group(1).strip()
                if validate_policy_number(policy_number) and policy_number not in policy_numbers:
                    policy_numbers.append(policy_number)
        
        # Try more general approach
        lines = text.split('\n')
        for line in lines:
            if 'policy' in line.lower():
                # Try to extract alphanumeric strings that could be policy numbers
                potential_numbers = re.findall(r'[A-Z0-9]{8,15}', line)
                for number in potential_numbers:
                    if validate_policy_number(number) and number not in policy_numbers:
                        policy_numbers.append(number)
                
                # Try with hyphens or spaces
                potential_numbers = re.findall(r'[A-Z0-9]{3,7}[-\s][A-Z0-9]{3,7}', line)
                for number in potential_numbers:
                    # Remove spaces and validate
                    clean_number = number.replace(' ', '').replace('-', '')
                    if validate_policy_number(clean_number) and clean_number not in policy_numbers:
                        policy_numbers.append(clean_number)
    
    except Exception as e:
        logger.error(f"Error extracting policy numbers: {str(e)}", exc_info=True)
    
    return policy_numbers

def normalize_policy_number(policy_number):
    """
    Normalize policy number format
    
    Args:
        policy_number: Policy number to normalize
        
    Returns:
        str: Normalized policy number
    """
    # Remove spaces and hyphens
    clean_number = policy_number.replace(' ', '').replace('-', '')
    
    # Convert to uppercase
    clean_number = clean_number.upper()
    
    return clean_number