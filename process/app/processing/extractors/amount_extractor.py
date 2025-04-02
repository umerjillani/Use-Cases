"""
Intelligent Document Processing System
Amount extraction
"""

import re
import logging
from decimal import Decimal, InvalidOperation

# Configure logging
logger = logging.getLogger(__name__)

# Patterns for monetary amounts
AMOUNT_PATTERNS = [
    # Currency symbol followed by amount with possible commas and decimal point
    r'[$€£¥]\s*([0-9,]+(?:\.[0-9]{2})?)',
    
    # Amount followed by currency symbol or code
    r'([0-9,]+(?:\.[0-9]{2})?)\s*[$€£¥]',
    r'([0-9,]+(?:\.[0-9]{2})?)\s*(?:USD|EUR|GBP|JPY)',
    
    # Words indicating an amount followed by number
    r'(?:amount|total|sum|payment)(?:\s+(?:of|:))?\s+[$€£¥]?\s*([0-9,]+(?:\.[0-9]{2})?)',
    
    # Check amount in words pattern
    r'(?:amount in words|written amount)(?:\s+(?:of|:))?\s+.*?([0-9,]+(?:\.[0-9]{2})?)',
]

# Words that could indicate an amount
AMOUNT_KEYWORDS = [
    'total', 'amount', 'payment', 'check', 'cheque', 'sum', 'paid', 'charge', 
    'fee', 'premium', 'balance', 'due', 'payable', 'price', 'cost'
]

def extract_amount(text):
    """
    Extract monetary amount from text
    
    Args:
        text: Text to extract amount from
        
    Returns:
        float: Extracted amount or None if not found
    """
    try:
        # Check if text is None or empty
        if not text:
            return None
        
        # Try regular expression patterns
        for pattern in AMOUNT_PATTERNS:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                amount_str = matches.group(1).strip()
                amount = parse_amount(amount_str)
                if amount is not None:
                    return amount
        
        # Look for lines containing amount keywords
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            
            # Check if line contains any amount keyword
            if any(keyword in line_lower for keyword in AMOUNT_KEYWORDS):
                # Extract all potential amounts from the line
                potential_amounts = re.findall(r'[$€£¥]?\s*([0-9,]+(?:\.[0-9]{2})?)', line)
                
                # Process each potential amount
                for amount_str in potential_amounts:
                    amount = parse_amount(amount_str)
                    if amount is not None:
                        return amount
        
        # If no amount found
        return None
    
    except Exception as e:
        logger.error(f"Error extracting amount: {str(e)}", exc_info=True)
        return None

def parse_amount(amount_str):
    """
    Parse amount string to float
    
    Args:
        amount_str: Amount string to parse
        
    Returns:
        float: Parsed amount or None if parsing fails
    """
    try:
        # Remove currency symbols and commas
        cleaned_str = amount_str.replace('$', '').replace('€', '').replace('£', '')
        cleaned_str = cleaned_str.replace('¥', '').replace(',', '')
        
        # Convert to decimal
        amount = Decimal(cleaned_str)
        
        # Convert to float
        return float(amount)
    
    except (InvalidOperation, ValueError) as e:
        logger.debug(f"Failed to parse amount '{amount_str}': {str(e)}")
        return None

def extract_amounts(text):
    """
    Extract all monetary amounts from text
    
    Args:
        text: Text to extract amounts from
        
    Returns:
        list: List of extracted amounts
    """
    amounts = []
    
    try:
        # Try regular expression patterns
        for pattern in AMOUNT_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).strip()
                amount = parse_amount(amount_str)
                if amount is not None and amount not in amounts:
                    amounts.append(amount)
        
        # Look for lines containing amount keywords
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            
            # Check if line contains any amount keyword
            if any(keyword in line_lower for keyword in AMOUNT_KEYWORDS):
                # Extract all potential amounts from the line
                potential_amounts = re.findall(r'[$€£¥]?\s*([0-9,]+(?:\.[0-9]{2})?)', line)
                
                # Process each potential amount
                for amount_str in potential_amounts:
                    amount = parse_amount(amount_str)
                    if amount is not None and amount not in amounts:
                        amounts.append(amount)
    
    except Exception as e:
        logger.error(f"Error extracting amounts: {str(e)}", exc_info=True)
    
    return amounts

def get_highest_amount(text):
    """
    Get the highest monetary amount from text
    
    Args:
        text: Text to extract amounts from
        
    Returns:
        float: Highest amount or None if no amounts found
    """
    amounts = extract_amounts(text)
    
    if amounts:
        return max(amounts)
    
    return None

def get_total_amount(text):
    """
    Attempt to find the total amount in the text
    
    Args:
        text: Text to extract total amount from
        
    Returns:
        float: Total amount or None if not found
    """
    try:
        # Look for lines containing total keywords
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            
            # Check if line contains total keywords
            if 'total' in line_lower or 'grand total' in line_lower:
                # Extract all potential amounts from the line
                potential_amounts = re.findall(r'[$€£¥]?\s*([0-9,]+(?:\.[0-9]{2})?)', line)
                
                # Process each potential amount
                for amount_str in potential_amounts:
                    amount = parse_amount(amount_str)
                    if amount is not None:
                        return amount
        
        # If no total found, fall back to highest amount
        return get_highest_amount(text)
    
    except Exception as e:
        logger.error(f"Error getting total amount: {str(e)}", exc_info=True)
        return None