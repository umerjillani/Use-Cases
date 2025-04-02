"""
Intelligent Document Processing System
Dashboard API routes
"""

import logging
from flask import Blueprint, jsonify, current_app

from app.services.document_service import DocumentService
from app.services.batch_service import BatchService
from app.services.exception_service import ExceptionService

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Get dashboard statistics
    
    Response:
        - documents: Document statistics
        - batches: Batch statistics with amount totals
        - exceptions: Exception statistics
    """
    try:
        # Get statistics from services
        document_stats = DocumentService.get_document_stats()
        batch_stats = BatchService.get_batch_stats()
        exception_stats = ExceptionService.get_exception_stats()
        
        # Get batch amount totals
        from app.models.batch import Batch
        from app import db
        
        # Calculate total processed amount across all batches
        total_amount = db.session.query(db.func.sum(Batch.total_amount)).scalar() or 0
        
        # Calculate total verified amount across all batches
        total_verified_amount = db.session.query(db.func.sum(Batch.verified_amount)).scalar() or 0
        
        # Add amount totals to batch stats
        batch_stats['total_amount'] = float(total_amount)
        batch_stats['total_verified_amount'] = float(total_verified_amount)
        
        # Combine stats
        stats = {
            'documents': document_stats,
            'batches': batch_stats,
            'exceptions': exception_stats
        }
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting dashboard statistics: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error getting dashboard statistics: {str(e)}"
        }), 500


@dashboard_bp.route('/recent-activity', methods=['GET'])
def get_recent_activity():
    """
    Get recent activity for dashboard
    
    Response:
        - documents: Recent documents
        - batches: Recent batches
        - exceptions: Recent exceptions
    """
    try:
        # Get recent documents (last 5)
        documents, _ = DocumentService.get_documents(limit=5)
        documents_data = [doc.to_dict() for doc in documents]
        
        # Get recent batches (last 5)
        batches, _ = BatchService.get_batches(limit=5)
        batches_data = [batch.to_dict() for batch in batches]
        
        # Get recent exceptions (last 5)
        exceptions, _ = ExceptionService.get_exceptions(limit=5)
        exceptions_data = [ex.to_dict() for ex in exceptions]
        
        return jsonify({
            'documents': documents_data,
            'batches': batches_data,
            'exceptions': exceptions_data
        })
    
    except Exception as e:
        logger.error(f"Error getting recent activity: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error getting recent activity: {str(e)}"
        }), 500


@dashboard_bp.route('/system-status', methods=['GET'])
def get_system_status():
    """
    Get system status
    
    Response:
        - status: System status
        - version: Application version
        - settings: Application settings
    """
    try:
        # Get system status
        status = {
            'status': 'online',
            'version': current_app.config.get('VERSION', '1.0.0'),
            'environment': current_app.config.get('ENV', 'production'),
            'settings': {
                'ocr_engine': current_app.config.get('OCR_ENGINE', 'tesseract'),
                'max_upload_size': current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
            }
        }
        
        return jsonify(status)
    
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error getting system status: {str(e)}"
        }), 500