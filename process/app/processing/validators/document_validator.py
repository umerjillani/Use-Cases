"""
Intelligent Document Processing System
Document validator
"""

import re
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Required fields for each document type
REQUIRED_FIELDS = {
    'claim': ['policy_number', 'claim_number', 'amount'],
    'agency_services': ['policy_number', 'agent_name'],
    'cancellation': ['policy_number', 'cancellation_reason', 'effective_date'],
    'mortgage_change': ['policy_number', 'loan_number', 'mortgagee_name'],
    'payment': ['policy_number', 'amount', 'payment_method']
}

# Field validation patterns
FIELD_PATTERNS = {
    'policy_number': r'^[A-Z0-9]{6,15}$',
    'claim_number': r'^[A-Z0-9]{5,15}$',
    'loan_number': r'^[A-Z0-9]{5,20}$',
    'amount': r'^[0-9]+(\.[0-9]{2})?$'
}

def validate_document(doc_type, extracted_data):
    """
    Validate extracted document data
    
    Args:
        doc_type: Document type
        extracted_data: Dictionary of extracted data
        
    Returns:
        dict: Validation result with keys:
            - is_valid: Boolean indicating if document is valid
            - confidence: Confidence score for validation
            - issues: List of validation issues
    """
    try:
        # Initialize result
        result = {
            'is_valid': True,
            'confidence': 1.0,
            'issues': []
        }
        
        # Check if document type is unknown or not supported
        if doc_type == 'unknown' or doc_type not in REQUIRED_FIELDS:
            result['is_valid'] = False
            result['confidence'] = 0.0
            result['issues'].append({
                'field': 'document_type',
                'message': f"Unknown or unsupported document type: {doc_type}",
                'severity': 'error'
            })
            return result
        
        # Check for required fields
        for field in REQUIRED_FIELDS[doc_type]:
            if field not in extracted_data or not extracted_data[field]:
                result['is_valid'] = False
                result['confidence'] -= 0.2  # Reduce confidence for each missing field
                result['issues'].append({
                    'field': field,
                    'message': f"Required field '{field}' is missing",
                    'severity': 'error'
                })
        
        # Validate fields that are present
        for field, value in extracted_data.items():
            # Skip empty values or fields not requiring validation
            if not value or field not in FIELD_PATTERNS:
                continue
            
            # Validate field format
            if not validate_field(field, value):
                result['is_valid'] = False
                result['confidence'] -= 0.1  # Reduce confidence for each invalid field
                result['issues'].append({
                    'field': field,
                    'message': f"Field '{field}' has invalid format: {value}",
                    'severity': 'warning'
                })
        
        # Perform document-specific validations
        if doc_type == 'claim':
            validate_claim_document(extracted_data, result)
        elif doc_type == 'payment':
            validate_payment_document(extracted_data, result)
        elif doc_type == 'cancellation':
            validate_cancellation_document(extracted_data, result)
        elif doc_type == 'mortgage_change':
            validate_mortgage_change_document(extracted_data, result)
        
        # Ensure confidence is between 0 and 1
        result['confidence'] = max(0.0, min(1.0, result['confidence']))
        
        return result
    
    except Exception as e:
        logger.error(f"Error validating document: {str(e)}", exc_info=True)
        return {
            'is_valid': False,
            'confidence': 0.0,
            'issues': [{
                'field': 'general',
                'message': f"Error during validation: {str(e)}",
                'severity': 'error'
            }]
        }

def validate_field(field, value):
    """
    Validate field value against pattern
    
    Args:
        field: Field name
        value: Field value
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Get pattern for field
        pattern = FIELD_PATTERNS.get(field)
        if not pattern:
            return True  # No pattern defined for field
        
        # Convert value to string if needed
        if not isinstance(value, str):
            value = str(value)
        
        # Validate against pattern
        return bool(re.match(pattern, value))
    
    except Exception as e:
        logger.error(f"Error validating field '{field}': {str(e)}", exc_info=True)
        return False

def validate_claim_document(data, result):
    """
    Validate claim document specific fields
    
    Args:
        data: Extracted data
        result: Validation result to update
    """
    # Check if amount is reasonable
    if 'amount' in data and data['amount']:
        try:
            amount = float(data['amount'])
            if amount <= 0:
                result['is_valid'] = False
                result['confidence'] -= 0.1
                result['issues'].append({
                    'field': 'amount',
                    'message': f"Claim amount must be positive: {amount}",
                    'severity': 'error'
                })
            elif amount > 1000000:  # Example: flag very large claims
                result['confidence'] -= 0.1
                result['issues'].append({
                    'field': 'amount',
                    'message': f"Unusually large claim amount: {amount}",
                    'severity': 'warning'
                })
        except ValueError:
            result['is_valid'] = False
            result['confidence'] -= 0.1
            result['issues'].append({
                'field': 'amount',
                'message': f"Invalid claim amount: {data['amount']}",
                'severity': 'error'
            })

def validate_payment_document(data, result):
    """
    Validate payment document specific fields
    
    Args:
        data: Extracted data
        result: Validation result to update
    """
    # Check if payment method is valid
    if 'payment_method' in data:
        valid_methods = ['check', 'credit_card', 'ach', 'wire', 'cash']
        if data['payment_method'] not in valid_methods and data['payment_method'] != 'unknown':
            result['confidence'] -= 0.1
            result['issues'].append({
                'field': 'payment_method',
                'message': f"Unrecognized payment method: {data['payment_method']}",
                'severity': 'warning'
            })

def validate_cancellation_document(data, result):
    """
    Validate cancellation document specific fields
    
    Args:
        data: Extracted data
        result: Validation result to update
    """
    # Check if effective date is in the future
    if 'effective_date' in data and data['effective_date']:
        try:
            effective_date = datetime.strptime(data['effective_date'], '%Y-%m-%d')
            if effective_date < datetime.now():
                result['confidence'] -= 0.1
                result['issues'].append({
                    'field': 'effective_date',
                    'message': f"Cancellation effective date is in the past: {data['effective_date']}",
                    'severity': 'warning'
                })
        except (ValueError, TypeError):
            result['confidence'] -= 0.1
            result['issues'].append({
                'field': 'effective_date',
                'message': f"Invalid cancellation effective date: {data['effective_date']}",
                'severity': 'warning'
            })

def validate_mortgage_change_document(data, result):
    """
    Validate mortgage change document specific fields
    
    Args:
        data: Extracted data
        result: Validation result to update
    """
    # Check if mortgagee name seems valid
    if 'mortgagee_name' in data and data['mortgagee_name']:
        if len(data['mortgagee_name']) < 3:
            result['confidence'] -= 0.1
            result['issues'].append({
                'field': 'mortgagee_name',
                'message': f"Mortgagee name seems too short: {data['mortgagee_name']}",
                'severity': 'warning'
            })