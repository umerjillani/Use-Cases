"""
Intelligent Document Processing System
Exception API routes
"""

import logging
from flask import Blueprint, request, jsonify
from app import db
from app.models.exception import Exception as DocException
from app.models.document import Document

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
exception_bp = Blueprint('exception', __name__, url_prefix='/api/exceptions')


@exception_bp.route('/', methods=['GET'])
@exception_bp.route('/list', methods=['GET'])  # Add alias route for frontend compatibility
def get_exceptions():
    """
    Get all exceptions
    
    Query parameters:
        - status: Filter by status
        - severity: Filter by severity
        - document_id: Filter by document ID
        - batch_id: Filter by batch ID
        - limit: Limit number of results
        - offset: Offset for pagination
        
    Response:
        - exceptions: List of exceptions
        - total: Total number of exceptions matching filters
    """
    try:
        # Get query parameters
        status = request.args.get('status')
        severity = request.args.get('severity')
        document_id = request.args.get('document_id')
        batch_id = request.args.get('batch_id')
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = DocException.query
        
        # Apply filters
        if status:
            query = query.filter(DocException.status == status)
        
        if severity:
            query = query.filter(DocException.severity == severity)
        
        if document_id:
            query = query.filter(DocException.document_id == document_id)
        
        if batch_id:
            query = query.filter(DocException.batch_id == batch_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        query = query.order_by(DocException.created_date.desc())
        query = query.limit(limit).offset(offset)
        
        # Get exceptions
        exceptions = query.all()
        
        # Convert to dictionaries
        exception_list = [ex.to_dict() for ex in exceptions]
        
        return jsonify({
            'exceptions': exception_list,
            'total': total
        })
    
    except Exception as e:
        logger.error(f"Error getting exceptions: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error getting exceptions: {str(e)}"
        }), 500


@exception_bp.route('/<int:exception_id>', methods=['GET'])
def get_exception(exception_id):
    """
    Get exception by ID
    
    Response:
        - exception: Exception data
    """
    try:
        # Get exception
        exception = DocException.query.get(exception_id)
        if not exception:
            return jsonify({
                'success': False,
                'message': f"Exception with ID {exception_id} not found"
            }), 404
        
        return jsonify({
            'exception': exception.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting exception: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error getting exception: {str(e)}"
        }), 500


@exception_bp.route('/<int:exception_id>/update-status', methods=['POST'])
def update_exception_status(exception_id):
    """
    Update exception status
    
    Request:
        - status: New exception status
        
    Response:
        - success: Boolean indicating if update was successful
        - exception: Updated exception data
        - message: Status message
    """
    try:
        # Get exception
        exception = DocException.query.get(exception_id)
        if not exception:
            return jsonify({
                'success': False,
                'message': f"Exception with ID {exception_id} not found"
            }), 404
        
        # Get new status
        status = request.json.get('status')
        if not status:
            return jsonify({
                'success': False,
                'message': "Status is required"
            }), 400
        
        # Validate status
        valid_statuses = ['open', 'in_progress', 'resolved']
        if status not in valid_statuses:
            return jsonify({
                'success': False,
                'message': f"Invalid status: {status}. Must be one of {', '.join(valid_statuses)}"
            }), 400
        
        # Update status
        exception.update_status(status)
        
        return jsonify({
            'success': True,
            'exception': exception.to_dict(),
            'message': f"Exception status updated to {status}"
        })
    
    except Exception as e:
        logger.error(f"Error updating exception status: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error updating exception status: {str(e)}"
        }), 500


@exception_bp.route('/resolve-all', methods=['POST'])
def resolve_all_exceptions():
    """
    Resolve all exceptions
    
    Request:
        - document_id: Optional document ID to filter exceptions
        - batch_id: Optional batch ID to filter exceptions
        
    Response:
        - success: Boolean indicating if resolution was successful
        - count: Number of exceptions resolved
        - message: Status message
    """
    try:
        # Get filters
        document_id = request.json.get('document_id')
        batch_id = request.json.get('batch_id')
        
        # Build query
        query = DocException.query.filter(DocException.status != 'resolved')
        
        # Apply filters
        if document_id:
            query = query.filter(DocException.document_id == document_id)
        
        if batch_id:
            query = query.filter(DocException.batch_id == batch_id)
        
        # Get exceptions
        exceptions = query.all()
        
        # Update status for each exception
        count = 0
        for exception in exceptions:
            exception.update_status('resolved')
            count += 1
        
        return jsonify({
            'success': True,
            'count': count,
            'message': f"Resolved {count} exceptions"
        })
    
    except Exception as e:
        logger.error(f"Error resolving exceptions: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error resolving exceptions: {str(e)}"
        }), 500


@exception_bp.route('/', methods=['POST'])
def create_exception():
    """
    Create a new exception
    
    Request:
        - exception_type: Type of exception
        - message: Exception message
        - document_id: Document ID
        - field_name: Optional field name with issue
        - severity: Optional severity level (info, warning, error)
        - details: Optional additional details
        
    Response:
        - success: Boolean indicating if creation was successful
        - exception: Created exception data
        - message: Status message
    """
    try:
        # Get required fields
        exception_type = request.json.get('exception_type')
        message = request.json.get('message')
        document_id = request.json.get('document_id')
        
        # Validate required fields
        if not exception_type:
            return jsonify({
                'success': False,
                'message': "Exception type is required"
            }), 400
        
        if not message:
            return jsonify({
                'success': False,
                'message': "Exception message is required"
            }), 400
        
        if not document_id:
            return jsonify({
                'success': False,
                'message': "Document ID is required"
            }), 400
        
        # Check if document exists
        document = Document.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f"Document with ID {document_id} not found"
            }), 404
        
        # Get optional fields
        field_name = request.json.get('field_name')
        severity = request.json.get('severity', 'warning')
        details = request.json.get('details')
        
        # Create exception
        exception = DocException(
            exception_type=exception_type,
            message=message,
            document_id=document_id,
            field_name=field_name,
            severity=severity
        )
        
        # Set details if provided
        if details:
            exception.set_details(details)
        
        db.session.add(exception)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'exception': exception.to_dict(),
            'message': "Exception created successfully"
        })
    
    except Exception as e:
        logger.error(f"Error creating exception: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error creating exception: {str(e)}"
        }), 500


@exception_bp.route('/<int:exception_id>', methods=['DELETE'])
def delete_exception(exception_id):
    """
    Delete exception
    
    Response:
        - success: Boolean indicating if deletion was successful
        - message: Status message
    """
    try:
        # Get exception
        exception = DocException.query.get(exception_id)
        if not exception:
            return jsonify({
                'success': False,
                'message': f"Exception with ID {exception_id} not found"
            }), 404
        
        # Delete exception
        db.session.delete(exception)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': "Exception deleted successfully"
        })
    
    except Exception as e:
        logger.error(f"Error deleting exception: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error deleting exception: {str(e)}"
        }), 500