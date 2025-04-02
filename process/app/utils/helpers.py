"""
Intelligent Document Processing System
Helper functions
"""

import os
import re
import json
import logging
import xml.dom.minidom
import xml.etree.ElementTree as ET
from datetime import datetime, date
from decimal import Decimal

# Configure logging
logger = logging.getLogger(__name__)

class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for handling special types
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super().default(obj)

def to_json(data, pretty=False):
    """
    Convert data to JSON string
    
    Args:
        data: Data to convert
        pretty: Whether to format JSON with indentation
        
    Returns:
        str: JSON string
    """
    try:
        if pretty:
            return json.dumps(data, cls=CustomJSONEncoder, indent=2, sort_keys=True)
        else:
            return json.dumps(data, cls=CustomJSONEncoder)
    except Exception as e:
        logger.error(f"Error converting to JSON: {str(e)}", exc_info=True)
        return "{}"

def from_json(json_str):
    """
    Convert JSON string to data
    
    Args:
        json_str: JSON string
        
    Returns:
        dict: Parsed JSON data
    """
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error parsing JSON: {str(e)}", exc_info=True)
        return {}

def to_xml(data, root_name="root"):
    """
    Convert data to XML string
    
    Args:
        data: Data to convert
        root_name: Name of root element
        
    Returns:
        str: XML string
    """
    try:
        def _build_xml(parent, data):
            if isinstance(data, dict):
                for key, value in data.items():
                    # Create valid XML element name
                    key = re.sub(r'[^a-zA-Z0-9_]', '_', str(key))
                    if not key:
                        key = "item"
                    
                    # Handle None values
                    if value is None:
                        elem = ET.SubElement(parent, key)
                    # Handle lists
                    elif isinstance(value, list):
                        elem = ET.SubElement(parent, key)
                        for item in value:
                            item_elem = ET.SubElement(elem, "item")
                            _build_xml(item_elem, item)
                    # Handle nested dictionaries
                    elif isinstance(value, dict):
                        elem = ET.SubElement(parent, key)
                        _build_xml(elem, value)
                    # Handle basic types
                    else:
                        elem = ET.SubElement(parent, key)
                        elem.text = str(value)
            else:
                # Handle non-dict values at root
                parent.text = str(data)
        
        # Create root element
        root = ET.Element(root_name)
        _build_xml(root, data)
        
        # Convert to string and prettify
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = xml.dom.minidom.parseString(rough_string)
        pretty_string = reparsed.toprettyxml(indent="  ")
        
        return pretty_string
    
    except Exception as e:
        logger.error(f"Error converting to XML: {str(e)}", exc_info=True)
        return f"<{root_name}></{root_name}>"

def from_xml(xml_str):
    """
    Convert XML string to data
    
    Args:
        xml_str: XML string
        
    Returns:
        dict: Parsed XML data
    """
    try:
        def _parse_element(element):
            result = {}
            
            # Process attributes
            for key, value in element.attrib.items():
                result[f"@{key}"] = value
            
            # Process child elements
            for child in element:
                child_data = _parse_element(child)
                
                if child.tag in result:
                    # If tag already exists, convert to list if not already
                    if isinstance(result[child.tag], list):
                        result[child.tag].append(child_data)
                    else:
                        result[child.tag] = [result[child.tag], child_data]
                else:
                    result[child.tag] = child_data
            
            # Process text content
            if element.text and element.text.strip():
                if result:
                    result["#text"] = element.text.strip()
                else:
                    return element.text.strip()
            
            return result if result else None
        
        root = ET.fromstring(xml_str)
        return {root.tag: _parse_element(root)}
    
    except Exception as e:
        logger.error(f"Error parsing XML: {str(e)}", exc_info=True)
        return {}

def format_currency(amount):
    """
    Format amount as currency string
    
    Args:
        amount: Amount to format
        
    Returns:
        str: Formatted currency string
    """
    try:
        if amount is None:
            return "$0.00"
        
        return "${:,.2f}".format(float(amount))
    except (ValueError, TypeError) as e:
        logger.error(f"Error formatting currency: {str(e)}", exc_info=True)
        return "$0.00"

def format_phone(phone):
    """
    Format phone number
    
    Args:
        phone: Phone number to format
        
    Returns:
        str: Formatted phone number
    """
    try:
        if not phone:
            return ""
        
        # Remove non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) == 10:
            # Format as (XXX) XXX-XXXX
            return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11 and digits[0] == '1':
            # Format as 1-XXX-XXX-XXXX
            return f"1-{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
        else:
            # Return as is
            return phone
    
    except Exception as e:
        logger.error(f"Error formatting phone number: {str(e)}", exc_info=True)
        return phone

def format_date(date_str, input_format=None, output_format="%m/%d/%Y"):
    """
    Format date string
    
    Args:
        date_str: Date string to format
        input_format: Input date format (or None for auto-detect)
        output_format: Output date format
        
    Returns:
        str: Formatted date string
    """
    try:
        if not date_str:
            return ""
        
        # Convert date object to string
        if isinstance(date_str, (datetime, date)):
            return date_str.strftime(output_format)
        
        # Try specific format if provided
        if input_format:
            dt = datetime.strptime(date_str, input_format)
            return dt.strftime(output_format)
        
        # Try common formats
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime(output_format)
            except ValueError:
                continue
        
        # If all attempts fail, return original string
        return date_str
    
    except Exception as e:
        logger.error(f"Error formatting date: {str(e)}", exc_info=True)
        return date_str

def truncate_text(text, max_length=100, suffix="..."):
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add to truncated text
        
    Returns:
        str: Truncated text
    """
    try:
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        # Truncate at word boundary
        truncated = text[:max_length].rsplit(' ', 1)[0]
        return truncated + suffix
    
    except Exception as e:
        logger.error(f"Error truncating text: {str(e)}", exc_info=True)
        return text[:max_length] + suffix if len(text) > max_length else text

def get_file_size_str(size_bytes):
    """
    Get human-readable file size
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        str: Human-readable file size
    """
    try:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    except Exception as e:
        logger.error(f"Error getting file size string: {str(e)}", exc_info=True)
        return f"{size_bytes} B"

def get_document_type_display(doc_type):
    """
    Get display name for document type
    
    Args:
        doc_type: Document type code
        
    Returns:
        str: Document type display name
    """
    display_names = {
        'claim': 'Insurance Claim',
        'agency_services': 'Agency Services',
        'cancellation': 'Policy Cancellation',
        'mortgage_change': 'Mortgage Change',
        'payment': 'Payment',
        'unknown': 'Unknown Document Type'
    }
    
    return display_names.get(doc_type, doc_type.replace('_', ' ').title())

def generate_batch_name():
    """
    Generate a new batch name
    
    Returns:
        str: Generated batch name
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"Batch_{timestamp}"

def mask_sensitive_data(text, patterns=None):
    """
    Mask sensitive data in text
    
    Args:
        text: Text to mask
        patterns: Dictionary of patterns and replacement functions
        
    Returns:
        str: Masked text
    """
    try:
        if not text:
            return ""
        
        if patterns is None:
            patterns = {
                # SSN: XXX-XX-XXXX
                r'\b\d{3}-\d{2}-\d{4}\b': lambda m: f"XXX-XX-{m.group(0)[-4:]}",
                
                # Credit Card: XXXX XXXX XXXX XXXX
                r'\b(?:\d{4}[- ]){3}\d{4}\b': lambda m: f"XXXX-XXXX-XXXX-{m.group(0)[-4:]}",
                
                # Phone: (XXX) XXX-XXXX
                r'\(\d{3}\)\s*\d{3}-\d{4}': lambda m: f"(XXX) XXX-{m.group(0)[-4:]}",
                
                # Email: user@domain.com
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': 
                    lambda m: f"{m.group(0)[0]}XXXX@{m.group(0).split('@')[1]}"
            }
        
        masked_text = text
        for pattern, replacement_func in patterns.items():
            masked_text = re.sub(pattern, replacement_func, masked_text)
        
        return masked_text
    
    except Exception as e:
        logger.error(f"Error masking sensitive data: {str(e)}", exc_info=True)
        return text

def get_progress_percentage(current, total):
    """
    Calculate progress percentage
    
    Args:
        current: Current progress
        total: Total expected
        
    Returns:
        int: Progress percentage (0-100)
    """
    try:
        if total <= 0:
            return 0
        
        percentage = int((current / total) * 100)
        return min(100, max(0, percentage))  # Clamp between 0-100
    
    except Exception as e:
        logger.error(f"Error calculating progress percentage: {str(e)}", exc_info=True)
        return 0