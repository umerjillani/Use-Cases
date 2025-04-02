"""
Intelligent Document Processing System
Document API routes
"""

import os
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from app import db
from app.models.document import Document
from app.models.exception import Exception as DocException

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
document_bp = Blueprint('document', __name__, url_prefix='/api/documents')


@document_bp.route('/', methods=['GET'])
def get_documents():
    """
    Get all documents
    
    Query parameters:
        - status: Filter by status
        - document_type: Filter by document type
        - batch_id: Filter by batch ID
        - is_valid: Filter by validation status
        - limit: Limit number of results
        - offset: Offset for pagination
        
    Response:
        - documents: List of documents
        - total: Total number of documents matching filters
    """
    try:
        # Get query parameters
        status = request.args.get('status')
        document_type = request.args.get('document_type')
        batch_id = request.args.get('batch_id')
        is_valid = request.args.get('is_valid')
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Document.query
        
        # Apply filters
        if status:
            query = query.filter(Document.status == status)
        
        if document_type:
            query = query.filter(Document.document_type == document_type)
        
        if batch_id:
            query = query.filter(Document.batch_id == batch_id)
        
        if is_valid is not None:
            is_valid_bool = is_valid.lower() == 'true'
            query = query.filter(Document.is_valid == is_valid_bool)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        query = query.order_by(Document.upload_date.desc())
        query = query.limit(limit).offset(offset)
        
        # Get documents
        documents = query.all()
        
        # Convert to dictionaries
        document_list = [doc.to_dict() for doc in documents]
        
        return jsonify({
            'documents': document_list,
            'total': total
        })
    
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error getting documents: {str(e)}"
        }), 500


@document_bp.route('/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """
    Get document by ID
    
    Response:
        - document: Document data
    """
    try:
        # Get document
        document = Document.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f"Document with ID {document_id} not found"
            }), 404
        
        return jsonify({
            'document': document.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error getting document: {str(e)}"
        }), 500


@document_bp.route('/<int:document_id>/download', methods=['GET'])
def download_document(document_id):
    """
    Download document file
    """
    try:
        # Get document
        document = Document.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f"Document with ID {document_id} not found"
            }), 404
        
        # Check if file exists
        file_path = document.original_path
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': f"Document file not found"
            }), 404
        
        # Return file
        return send_file(file_path, download_name=document.filename)
    
    except Exception as e:
        logger.error(f"Error downloading document: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error downloading document: {str(e)}"
        }), 500


@document_bp.route('/<int:document_id>/exceptions', methods=['GET'])
def get_document_exceptions(document_id):
    """
    Get exceptions for document
    
    Response:
        - exceptions: List of exceptions
    """
    try:
        # Get document
        document = Document.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f"Document with ID {document_id} not found"
            }), 404
        
        # Get exceptions
        exceptions = DocException.query.filter_by(document_id=document_id).all()
        
        # Convert to dictionaries
        exception_list = [ex.to_dict() for ex in exceptions]
        
        return jsonify({
            'exceptions': exception_list
        })
    
    except Exception as e:
        logger.error(f"Error getting document exceptions: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error getting document exceptions: {str(e)}"
        }), 500


@document_bp.route('/<int:document_id>/update-type', methods=['POST'])
def update_document_type(document_id):
    """
    Update document type
    
    Request:
        - document_type: New document type
        
    Response:
        - success: Boolean indicating if update was successful
        - document: Updated document data
        - message: Status message
    """
    try:
        # Get document
        document = Document.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f"Document with ID {document_id} not found"
            }), 404
        
        # Get new document type
        document_type = request.json.get('document_type')
        if not document_type:
            return jsonify({
                'success': False,
                'message': "Document type is required"
            }), 400
        
        # Update document type
        document.document_type = document_type
        db.session.commit()
        
        return jsonify({
            'success': True,
            'document': document.to_dict(),
            'message': 'Document type updated successfully'
        })
    
    except Exception as e:
        logger.error(f"Error updating document type: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error updating document type: {str(e)}"
        }), 500


@document_bp.route('/<int:document_id>/assign-batch', methods=['POST'])
def assign_document_to_batch(document_id):
    """
    Assign document to batch
    
    Request:
        - batch_id: ID of batch to assign to
        
    Response:
        - success: Boolean indicating if assignment was successful
        - document: Updated document data
        - message: Status message
    """
    try:
        # Get document
        document = Document.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f"Document with ID {document_id} not found"
            }), 404
        
        # Get batch ID
        batch_id = request.json.get('batch_id')
        if batch_id is None:
            return jsonify({
                'success': False,
                'message': "Batch ID is required"
            }), 400
        
        # Check if batch exists
        from app.models.batch import Batch
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({
                'success': False,
                'message': f"Batch with ID {batch_id} not found"
            }), 404
        
        # Assign document to batch
        batch.add_document(document)
        
        return jsonify({
            'success': True,
            'document': document.to_dict(),
            'message': f"Document assigned to batch {batch_id} successfully"
        })
    
    except Exception as e:
        logger.error(f"Error assigning document to batch: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error assigning document to batch: {str(e)}"
        }), 500


@document_bp.route('/<int:document_id>/remove-from-batch', methods=['POST'])
def remove_document_from_batch(document_id):
    """
    Remove document from batch
    
    Response:
        - success: Boolean indicating if removal was successful
        - document: Updated document data
        - message: Status message
    """
    try:
        # Get document
        document = Document.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f"Document with ID {document_id} not found"
            }), 404
        
        # Check if document is assigned to a batch
        if not document.batch_id:
            return jsonify({
                'success': False,
                'message': "Document is not assigned to a batch"
            }), 400
        
        # Get batch
        from app.models.batch import Batch
        batch = Batch.query.get(document.batch_id)
        
        # Remove document from batch
        if batch:
            batch.remove_document(document)
        else:
            # If batch not found, just clear the batch_id
            document.batch_id = None
            db.session.commit()
        
        return jsonify({
            'success': True,
            'document': document.to_dict(),
            'message': "Document removed from batch successfully"
        })
    
    except Exception as e:
        logger.error(f"Error removing document from batch: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error removing document from batch: {str(e)}"
        }), 500


@document_bp.route('/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """
    Delete document
    
    Response:
        - success: Boolean indicating if deletion was successful
        - message: Status message
    """
    try:
        # Get document
        document = Document.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f"Document with ID {document_id} not found"
            }), 404
        
        # Delete file if it exists
        if document.original_path and os.path.exists(document.original_path):
            os.remove(document.original_path)
        
        if document.processed_path and os.path.exists(document.processed_path):
            os.remove(document.processed_path)
        
        # Delete document
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': "Document deleted successfully"
        })
    
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error deleting document: {str(e)}"
        }), 500