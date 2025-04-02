"""
Intelligent Document Processing System
Date extraction
"""

import re
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Date patterns
DATE_PATTERNS = [
    # MM/DD/YYYY or MM-DD-YYYY
    (r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', '%m/%d/%Y'),
    
    # YYYY/MM/DD or YYYY-MM-DD
    (r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})', '%Y/%m/%d'),
    
    # Month DD, YYYY
    (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})', '%B %d %Y'),
    
    # DD Month YYYY
    (r'(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+(\d{4})', '%d %B %Y'),
    
    # Month YYYY (no day)
    (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', '%B %Y'),
    
    # MM/DD/YY or MM-DD-YY
    (r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2})', '%m/%d/%y'),
    
    # Mon DD, YYYY (abbreviated month)
    (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})', '%b %d %Y'),
]

# Date labels that might appear near dates
DATE_LABELS = [
    'effective date', 'issue date', 'policy date', 'expiration date', 'inception date',
    'date of loss', 'claim date', 'report date', 'transaction date', 'processing date',
    'date of birth', 'signature date', 'cancellation date', 'renewal date', 'termination date',
    'payment date', 'due date', 'effective', 'expires', 'issued', 'processed'
]

def extract_dates(text):
    """
    Extract dates from text
    
    Args:
        text: Text to extract dates from
        
    Returns:
        list: List of extracted dates with format:
            [
                {
                    'date': 'YYYY-MM-DD',
                    'original': 'original date string',
                    'label': 'date label if found',
                    'position': position in text
                },
                ...
            ]
    """
    try:
        # Check if text is None or empty
        if not text:
            return []
        
        # Split text into lines
        lines = text.split('\n')
        
        dates = []
        
        # Process each line
        for line_num, line in enumerate(lines):
            # Look for dates with labels
            for label in DATE_LABELS:
                # Look for label in line (case insensitive)
                if label.lower() in line.lower():
                    # Extract date from line
                    extracted_date = extract_date_from_line(line)
                    if extracted_date:
                        dates.append({
                            'date': extracted_date['date'],
                            'original': extracted_date['original'],
                            'label': label,
                            'position': extracted_date['position'] + sum(len(l) + 1 for l in lines[:line_num])
                        })
                        break  # Only one label per line
            
            # Also extract dates without labels
            extracted_dates = extract_dates_from_line(line)
            for extracted_date in extracted_dates:
                # Check if this date is already captured with a label
                if not any(d['original'] == extracted_date['original'] and 
                           d['position'] == extracted_date['position'] + sum(len(l) + 1 for l in lines[:line_num]) 
                           for d in dates):
                    dates.append({
                        'date': extracted_date['date'],
                        'original': extracted_date['original'],
                        'label': None,
                        'position': extracted_date['position'] + sum(len(l) + 1 for l in lines[:line_num])
                    })
        
        # Deduplicate dates
        unique_dates = []
        seen_dates = set()
        
        for date in dates:
            if date['date'] not in seen_dates:
                seen_dates.add(date['date'])
                unique_dates.append(date)
        
        return unique_dates
    
    except Exception as e:
        logger.error(f"Error extracting dates: {str(e)}", exc_info=True)
        return []

def extract_date_from_line(line):
    """
    Extract first date from a line of text
    
    Args:
        line: Line of text
        
    Returns:
        dict: Extracted date or None if not found
    """
    try:
        for pattern, date_format in DATE_PATTERNS:
            matches = re.search(pattern, line)
            if matches:
                date_str = matches.group(0)
                
                try:
                    # For patterns with month names
                    if '%B' in date_format or '%b' in date_format:
                        if len(matches.groups()) == 2:  # Month YYYY (no day)
                            month, year = matches.groups()
                            # Use first day of month
                            parsed_date = datetime.strptime(f"{month} 1 {year}", "%B %d %Y")
                        else:
                            # Full date with month name
                            parsed_date = datetime.strptime(date_str, date_format.replace('/', ''))
                    else:
                        # For numeric patterns
                        if '/' in date_str:
                            sep = '/'
                        elif '-' in date_str:
                            sep = '-'
                        else:
                            sep = '/'
                        
                        if date_format == '%m/%d/%Y':
                            month, day, year = matches.groups()
                            parsed_date = datetime.strptime(f"{month}{sep}{day}{sep}{year}", date_format.replace('/', sep))
                        elif date_format == '%Y/%m/%d':
                            year, month, day = matches.groups()
                            parsed_date = datetime.strptime(f"{year}{sep}{month}{sep}{day}", date_format.replace('/', sep))
                        elif date_format == '%m/%d/%y':
                            month, day, year = matches.groups()
                            # Adjust two-digit year
                            if int(year) > 50:  # Assume 1900s for years > 50
                                year = f"19{year}"
                            else:  # Assume 2000s for years <= 50
                                year = f"20{year}"
                            parsed_date = datetime.strptime(f"{month}{sep}{day}{sep}{year}", '%m/%d/%Y')
                        else:
                            parsed_date = datetime.strptime(date_str, date_format.replace('/', sep))
                    
                    return {
                        'date': parsed_date.strftime('%Y-%m-%d'),
                        'original': date_str,
                        'position': matches.start()
                    }
                except ValueError:
                    # Continue to next pattern if date is invalid
                    continue
        
        return None
    
    except Exception as e:
        logger.error(f"Error extracting date from line: {str(e)}", exc_info=True)
        return None

def extract_dates_from_line(line):
    """
    Extract all dates from a line of text
    
    Args:
        line: Line of text
        
    Returns:
        list: List of extracted dates
    """
    dates = []
    
    try:
        for pattern, date_format in DATE_PATTERNS:
            matches = re.finditer(pattern, line)
            for match in matches:
                date_str = match.group(0)
                
                try:
                    # For patterns with month names
                    if '%B' in date_format or '%b' in date_format:
                        if len(match.groups()) == 2:  # Month YYYY (no day)
                            month, year = match.groups()
                            # Use first day of month
                            parsed_date = datetime.strptime(f"{month} 1 {year}", "%B %d %Y")
                        else:
                            # Full date with month name
                            parsed_date = datetime.strptime(date_str, date_format.replace('/', ''))
                    else:
                        # For numeric patterns
                        if '/' in date_str:
                            sep = '/'
                        elif '-' in date_str:
                            sep = '-'
                        else:
                            sep = '/'
                        
                        if date_format == '%m/%d/%Y':
                            month, day, year = match.groups()
                            parsed_date = datetime.strptime(f"{month}{sep}{day}{sep}{year}", date_format.replace('/', sep))
                        elif date_format == '%Y/%m/%d':
                            year, month, day = match.groups()
                            parsed_date = datetime.strptime(f"{year}{sep}{month}{sep}{day}", date_format.replace('/', sep))
                        elif date_format == '%m/%d/%y':
                            month, day, year = match.groups()
                            # Adjust two-digit year
                            if int(year) > 50:  # Assume 1900s for years > 50
                                year = f"19{year}"
                            else:  # Assume 2000s for years <= 50
                                year = f"20{year}"
                            parsed_date = datetime.strptime(f"{month}{sep}{day}{sep}{year}", '%m/%d/%Y')
                        else:
                            parsed_date = datetime.strptime(date_str, date_format.replace('/', sep))
                    
                    dates.append({
                        'date': parsed_date.strftime('%Y-%m-%d'),
                        'original': date_str,
                        'position': match.start()
                    })
                except ValueError:
                    # Skip invalid dates
                    continue
        
        return dates
    
    except Exception as e:
        logger.error(f"Error extracting dates from line: {str(e)}", exc_info=True)
        return []

def parse_date(date_str):
    """
    Parse date string to standard format
    
    Args:
        date_str: Date string to parse
        
    Returns:
        str: Date in YYYY-MM-DD format or None if parsing fails
    """
    try:
        for pattern, date_format in DATE_PATTERNS:
            if re.match(pattern, date_str):
                try:
                    # For patterns with month names
                    if '%B' in date_format or '%b' in date_format:
                        parsed_date = datetime.strptime(date_str, date_format.replace('/', ''))
                    else:
                        # For numeric patterns
                        if '/' in date_str:
                            sep = '/'
                        elif '-' in date_str:
                            sep = '-'
                        else:
                            sep = '/'
                        
                        parsed_date = datetime.strptime(date_str, date_format.replace('/', sep))
                    
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    # Try next pattern
                    continue
        
        return None
    
    except Exception as e:
        logger.error(f"Error parsing date: {str(e)}", exc_info=True)
        return None

def is_date_valid(date_str):
    """
    Check if date string is valid
    
    Args:
        date_str: Date string to check
        
    Returns:
        bool: True if valid, False otherwise
    """
    return parse_date(date_str) is not None

def get_date_label(text, date_position):
    """
    Get label for date based on surrounding text
    
    Args:
        text: Full text
        date_position: Position of date in text
        
    Returns:
        str: Date label or None if not found
    """
    try:
        # Look at text before date (up to 50 characters)
        before_text = text[max(0, date_position - 50):date_position].lower()
        
        for label in DATE_LABELS:
            if label.lower() in before_text:
                return label
        
        return None
    
    except Exception as e:
        logger.error(f"Error getting date label: {str(e)}", exc_info=True)
        return None