"""
Intelligent Document Processing System
Batch API routes
"""

import os
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.batch import Batch
from app.models.document import Document
from app.models.exception import Exception as DocException

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
batch_bp = Blueprint('batch', __name__, url_prefix='/api/batches')


@batch_bp.route('/', methods=['GET'])
@batch_bp.route('/list', methods=['GET'])  # Add alias route for frontend compatibility
def get_batches():
    """
    Get all batches
    
    Query parameters:
        - status: Filter by status
        - limit: Limit number of results
        - offset: Offset for pagination
        
    Response:
        - batches: List of batches
        - total: Total number of batches matching filters
    """
    try:
        # Get query parameters
        status = request.args.get('status')
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Batch.query
        
        # Apply filters
        if status:
            query = query.filter(Batch.status == status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        query = query.order_by(Batch.creation_date.desc())
        query = query.limit(limit).offset(offset)
        
        # Get batches
        batches = query.all()
        
        # Convert to dictionaries
        batch_list = [batch.to_dict() for batch in batches]
        
        return jsonify({
            'batches': batch_list,
            'total': total
        })
    
    except Exception as e:
        logger.error(f"Error getting batches: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error getting batches: {str(e)}"
        }), 500


@batch_bp.route('/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    """
    Get batch by ID
    
    Response:
        - batch: Batch data
    """
    try:
        # Get batch
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({
                'success': False,
                'message': f"Batch with ID {batch_id} not found"
            }), 404
        
        return jsonify({
            'batch': batch.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting batch: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error getting batch: {str(e)}"
        }), 500


@batch_bp.route('/', methods=['POST'])
def create_batch():
    """
    Create new batch
    
    Request:
        - name: Batch name
        - document_ids: Optional list of document IDs to add to batch
        
    Response:
        - success: Boolean indicating if creation was successful
        - batch: Created batch data
        - message: Status message
    """
    try:
        # Get batch name
        name = request.json.get('name')
        if not name:
            return jsonify({
                'success': False,
                'message': "Batch name is required"
            }), 400
        
        # Create batch
        batch = Batch(name=name)
        db.session.add(batch)
        db.session.commit()
        
        # Add documents to batch if provided
        document_ids = request.json.get('document_ids', [])
        for document_id in document_ids:
            document = Document.query.get(document_id)
            if document:
                batch.add_document(document)
        
        return jsonify({
            'success': True,
            'batch': batch.to_dict(),
            'message': 'Batch created successfully'
        })
    
    except Exception as e:
        logger.error(f"Error creating batch: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error creating batch: {str(e)}"
        }), 500


@batch_bp.route('/<int:batch_id>', methods=['PUT'])
def update_batch(batch_id):
    """
    Update batch
    
    Request:
        - name: New batch name
        - status: New batch status
        - verified_amount: New verified amount
        
    Response:
        - success: Boolean indicating if update was successful
        - batch: Updated batch data
        - message: Status message
    """
    try:
        # Get batch
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({
                'success': False,
                'message': f"Batch with ID {batch_id} not found"
            }), 404
        
        # Update batch name if provided
        name = request.json.get('name')
        if name:
            batch.name = name
        
        # Update batch status if provided
        status = request.json.get('status')
        if status:
            batch.update_status(status)
        
        # Update verified amount if provided
        verified_amount = request.json.get('verified_amount')
        if verified_amount is not None:
            batch.set_verified_amount(verified_amount)
        
        # Update metadata if provided
        metadata = request.json.get('metadata')
        if metadata:
            batch.set_metadata(metadata)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'batch': batch.to_dict(),
            'message': 'Batch updated successfully'
        })
    
    except Exception as e:
        logger.error(f"Error updating batch: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error updating batch: {str(e)}"
        }), 500


@batch_bp.route('/<int:batch_id>/documents', methods=['GET'])
def get_batch_documents(batch_id):
    """
    Get documents in batch
    
    Response:
        - documents: List of documents in batch
        - total_amount: Total amount of checks in the batch
    """
    try:
        # Get batch
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({
                'success': False,
                'message': f"Batch with ID {batch_id} not found"
            }), 404
        
        # Get documents
        documents = Document.query.filter_by(batch_id=batch_id).all()
        
        # Convert to dictionaries
        document_list = [doc.to_dict() for doc in documents]
        
        # Calculate total amount of checks
        total_amount = batch.total_amount
        
        return jsonify({
            'documents': document_list,
            'total_amount': total_amount
        })
    
    except Exception as e:
        logger.error(f"Error getting batch documents: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error getting batch documents: {str(e)}"
        }), 500


@batch_bp.route('/<int:batch_id>/add-documents', methods=['POST'])
def add_documents_to_batch(batch_id):
    """
    Add documents to batch
    
    Request:
        - document_ids: List of document IDs to add to batch
        
    Response:
        - success: Boolean indicating if addition was successful
        - batch: Updated batch data
        - message: Status message
    """
    try:
        # Get batch
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({
                'success': False,
                'message': f"Batch with ID {batch_id} not found"
            }), 404
        
        # Get document IDs
        document_ids = request.json.get('document_ids', [])
        if not document_ids:
            return jsonify({
                'success': False,
                'message': "Document IDs are required"
            }), 400
        
        # Add documents to batch
        added_count = 0
        for document_id in document_ids:
            document = Document.query.get(document_id)
            if document:
                if document.batch_id == batch_id:
                    continue  # Skip if already in this batch
                elif document.batch_id:
                    # Remove from previous batch
                    prev_batch = Batch.query.get(document.batch_id)
                    if prev_batch:
                        prev_batch.remove_document(document)
                
                # Add to current batch
                batch.add_document(document)
                added_count += 1
        
        return jsonify({
            'success': True,
            'batch': batch.to_dict(),
            'message': f"Added {added_count} documents to batch"
        })
    
    except Exception as e:
        logger.error(f"Error adding documents to batch: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error adding documents to batch: {str(e)}"
        }), 500


@batch_bp.route('/<int:batch_id>/validate', methods=['POST'])
def validate_batch(batch_id):
    """
    Validate batch
    
    Request:
        - verified_amount: Optional verified amount for validation
        
    Response:
        - success: Boolean indicating if validation was successful
        - is_valid: Boolean indicating if batch is valid
        - issues: List of validation issues
        - message: Status message
    """
    try:
        # Get batch
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({
                'success': False,
                'message': f"Batch with ID {batch_id} not found"
            }), 404
        
        # Set verified amount if provided
        verified_amount = request.json.get('verified_amount')
        if verified_amount is not None:
            batch.set_verified_amount(verified_amount)
        
        # Validate batch
        issues = []
        
        # Check if batch has documents
        if batch.get_document_count() == 0:
            issues.append({
                'type': 'empty_batch',
                'message': 'Batch has no documents'
            })
        
        # Check if any documents have exceptions
        document_ids_with_exceptions = set()
        for exception in batch.exceptions:
            document_ids_with_exceptions.add(exception.document_id)
        
        if document_ids_with_exceptions:
            issues.append({
                'type': 'document_exceptions',
                'message': f'{len(document_ids_with_exceptions)} documents have exceptions',
                'document_ids': list(document_ids_with_exceptions)
            })
        
        # Check if amounts match
        if not batch.verify_amounts() and batch.verified_amount > 0:
            issues.append({
                'type': 'amount_mismatch',
                'message': f'Total amount {batch.total_amount} does not match verified amount {batch.verified_amount}',
                'total_amount': batch.total_amount,
                'verified_amount': batch.verified_amount
            })
        
        # Check if any documents are invalid
        invalid_documents = Document.query.filter_by(batch_id=batch_id, is_valid=False).all()
        if invalid_documents:
            issues.append({
                'type': 'invalid_documents',
                'message': f'{len(invalid_documents)} documents are invalid',
                'document_ids': [doc.id for doc in invalid_documents]
            })
        
        # Batch is valid if there are no issues
        is_valid = len(issues) == 0
        
        # Update batch status if valid
        if is_valid:
            batch.update_status('validated')
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'issues': issues,
            'message': 'Batch validation complete'
        })
    
    except Exception as e:
        logger.error(f"Error validating batch: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error validating batch: {str(e)}"
        }), 500


@batch_bp.route('/<int:batch_id>/exceptions', methods=['GET'])
def get_batch_exceptions(batch_id):
    """
    Get exceptions for batch
    
    Response:
        - exceptions: List of exceptions
    """
    try:
        # Get batch
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({
                'success': False,
                'message': f"Batch with ID {batch_id} not found"
            }), 404
        
        # Get exceptions
        exceptions = DocException.query.filter_by(batch_id=batch_id).all()
        
        # Convert to dictionaries
        exception_list = [ex.to_dict() for ex in exceptions]
        
        return jsonify({
            'exceptions': exception_list
        })
    
    except Exception as e:
        logger.error(f"Error getting batch exceptions: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error getting batch exceptions: {str(e)}"
        }), 500


@batch_bp.route('/<int:batch_id>', methods=['DELETE'])
def delete_batch(batch_id):
    """
    Delete batch
    
    Query parameters:
        - delete_documents: Whether to delete documents in batch (default: false)
        
    Response:
        - success: Boolean indicating if deletion was successful
        - message: Status message
    """
    try:
        # Get batch
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({
                'success': False,
                'message': f"Batch with ID {batch_id} not found"
            }), 404
        
        # Check if documents should be deleted
        delete_documents = request.args.get('delete_documents', 'false').lower() == 'true'
        
        if delete_documents:
            # Get all documents in batch
            documents = Document.query.filter_by(batch_id=batch_id).all()
            
            # Delete each document
            for document in documents:
                # Delete file if it exists
                if document.original_path and os.path.exists(document.original_path):
                    os.remove(document.original_path)
                
                if document.processed_path and os.path.exists(document.processed_path):
                    os.remove(document.processed_path)
                
                # Delete document
                db.session.delete(document)
        else:
            # Just remove batch association
            for document in batch.documents:
                document.batch_id = None
        
        # Delete batch
        db.session.delete(batch)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Batch deleted successfully{' with all documents' if delete_documents else ''}"
        })
    
    except Exception as e:
        logger.error(f"Error deleting batch: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error deleting batch: {str(e)}"
        }), 500  