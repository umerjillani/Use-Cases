"""
Intelligent Document Processing System
Document business logic
"""

import os
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

from app import db
from app.models.document import Document
from app.models.exception import Exception as DocException
from app.processing.document_processor import DocumentProcessor
from app.utils.file_utils import (
    save_uploaded_file,
    get_safe_filename,
    get_file_mime_type,
    get_file_hash,
    move_file,
    delete_file
)

# Configure logging
logger = logging.getLogger(__name__)


class DocumentService:
    """Service class for document operations"""
    
    @staticmethod
    def create_document(file, document_type='auto'):
        """
        Create a new document from uploaded file
        
        Args:
            file: Uploaded file object
            document_type: Type of document
            
        Returns:
            tuple: (document, message)
        """
        try:
            # Check if file is valid
            if not file or file.filename == '':
                return None, "No file selected"
            
            # Get file extension
            filename = file.filename
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else None
            
            # Check if file extension is allowed
            allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
            if ext not in allowed_extensions:
                return None, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            
            # Save file to upload folder
            upload_folder = current_app.config['UPLOAD_FOLDER']
            file_path = save_uploaded_file(file, upload_folder)
            
            # Create document record
            document = Document(
                filename=os.path.basename(file_path),
                original_path=file_path,
                document_type=document_type
            )
            
            db.session.add(document)
            db.session.commit()
            
            return document, "Document created successfully"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating document: {str(e)}", exc_info=True)
            return None, f"Error creating document: {str(e)}"
    
    @staticmethod
    def get_document(document_id):
        """
        Get document by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            Document: Document object
        """
        return Document.query.get(document_id)
    
    @staticmethod
    def get_documents(filters=None, limit=None, offset=None):
        """
        Get documents with optional filtering and pagination
        
        Args:
            filters: Dictionary of filter criteria
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            tuple: (documents, total_count)
        """
        try:
            # Start with base query
            query = Document.query
            
            # Apply filters
            if filters:
                if 'status' in filters:
                    query = query.filter(Document.status == filters['status'])
                
                if 'document_type' in filters:
                    query = query.filter(Document.document_type == filters['document_type'])
                
                if 'batch_id' in filters:
                    query = query.filter(Document.batch_id == filters['batch_id'])
                
                if 'is_valid' in filters:
                    query = query.filter(Document.is_valid == filters['is_valid'])
            
            # Get total count
            total_count = query.count()
            
            # Apply sorting
            query = query.order_by(Document.upload_date.desc())
            
            # Apply pagination
            if limit is not None:
                query = query.limit(limit)
            
            if offset is not None:
                query = query.offset(offset)
            
            # Execute query
            documents = query.all()
            
            return documents, total_count
        
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}", exc_info=True)
            return [], 0
    
    @staticmethod
    def process_document(document_id):
        """
        Process a document
        
        Args:
            document_id: Document ID
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Get document
            document = Document.query.get(document_id)
            if not document:
                return False, f"Document with ID {document_id} not found"
            
            # Check if document file exists
            if not os.path.exists(document.original_path):
                return False, f"Document file not found at {document.original_path}"
            
            # Process document
            processor = DocumentProcessor(current_app)
            result = processor.process_document(document_id)
            
            if result:
                return True, "Document processed successfully"
            else:
                return False, "Document processing failed"
        
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            return False, f"Error processing document: {str(e)}"
    
    @staticmethod
    def update_document_type(document_id, document_type):
        """
        Update document type
        
        Args:
            document_id: Document ID
            document_type: New document type
            
        Returns:
            tuple: (document, message)
        """
        try:
            # Get document
            document = Document.query.get(document_id)
            if not document:
                return None, f"Document with ID {document_id} not found"
            
            # Update document type
            document.document_type = document_type
            db.session.commit()
            
            return document, "Document type updated successfully"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating document type: {str(e)}", exc_info=True)
            return None, f"Error updating document type: {str(e)}"
    
    @staticmethod
    def delete_document(document_id, delete_file=True):
        """
        Delete document
        
        Args:
            document_id: Document ID
            delete_file: Whether to delete the document file
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Get document
            document = Document.query.get(document_id)
            if not document:
                return False, f"Document with ID {document_id} not found"
            
            # Delete file if requested
            if delete_file:
                if document.original_path and os.path.exists(document.original_path):
                    delete_file(document.original_path)
                
                if document.processed_path and os.path.exists(document.processed_path):
                    delete_file(document.processed_path)
            
            # Delete associated exceptions
            DocException.query.filter_by(document_id=document_id).delete()
            
            # Delete document record
            db.session.delete(document)
            db.session.commit()
            
            return True, "Document deleted successfully"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting document: {str(e)}", exc_info=True)
            return False, f"Error deleting document: {str(e)}"
    
    @staticmethod
    def get_document_exceptions(document_id):
        """
        Get exceptions for document
        
        Args:
            document_id: Document ID
            
        Returns:
            list: List of exceptions
        """
        try:
            return DocException.query.filter_by(document_id=document_id).order_by(DocException.created_date.desc()).all()
        
        except Exception as e:
            logger.error(f"Error getting document exceptions: {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    def create_document_exception(document_id, exception_type, message, field_name=None, severity='warning', details=None):
        """
        Create a new exception for document
        
        Args:
            document_id: Document ID
            exception_type: Exception type
            message: Exception message
            field_name: Name of field with issue (optional)
            severity: Exception severity (info, warning, error)
            details: Additional details (optional)
            
        Returns:
            tuple: (exception, message)
        """
        try:
            # Check if document exists
            document = Document.query.get(document_id)
            if not document:
                return None, f"Document with ID {document_id} not found"
            
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
            
            return exception, "Exception created successfully"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating document exception: {str(e)}", exc_info=True)
            return None, f"Error creating document exception: {str(e)}"
    
    @staticmethod
    def resolve_document_exceptions(document_id):
        """
        Resolve all exceptions for document
        
        Args:
            document_id: Document ID
            
        Returns:
            tuple: (count, message)
        """
        try:
            # Get open exceptions
            exceptions = DocException.query.filter_by(
                document_id=document_id,
                status='open'
            ).all()
            
            # Update status for each exception
            count = 0
            for exception in exceptions:
                exception.update_status('resolved')
                count += 1
            
            return count, f"Resolved {count} exceptions"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resolving document exceptions: {str(e)}", exc_info=True)
            return 0, f"Error resolving document exceptions: {str(e)}"
    
    @staticmethod
    def reprocess_document(document_id):
        """
        Reprocess a document
        
        Args:
            document_id: Document ID
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Get document
            document = Document.query.get(document_id)
            if not document:
                return False, f"Document with ID {document_id} not found"
            
            # Reset document status
            document.status = 'uploaded'
            document.processed_date = None
            document.is_valid = False
            document.confidence_score = 0.0
            document.extracted_data = None
            
            # Delete existing exceptions
            DocException.query.filter_by(document_id=document_id).delete()
            
            db.session.commit()
            
            # Process document
            return DocumentService.process_document(document_id)
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error reprocessing document: {str(e)}", exc_info=True)
            return False, f"Error reprocessing document: {str(e)}"
    
    @staticmethod
    def get_document_stats():
        """
        Get document statistics
        
        Returns:
            dict: Dictionary with document statistics
        """
        try:
            total = Document.query.count()
            processed = Document.query.filter(Document.status == 'completed').count()
            failed = Document.query.filter(Document.status == 'failed').count()
            valid = Document.query.filter(Document.is_valid == True).count()
            invalid = Document.query.filter(Document.is_valid == False, Document.status == 'completed').count()
            
            by_type = {}
            for doc_type in ['claim', 'agency_services', 'cancellation', 'mortgage_change', 'payment', 'auto', 'unknown']:
                count = Document.query.filter(Document.document_type == doc_type).count()
                if count > 0:
                    by_type[doc_type] = count
            
            return {
                'total': total,
                'processed': processed,
                'failed': failed,
                'valid': valid,
                'invalid': invalid,
                'by_type': by_type
            }
        
        except Exception as e:
            logger.error(f"Error getting document stats: {str(e)}", exc_info=True)
            return {
                'total': 0,
                'processed': 0,
                'failed': 0,
                'valid': 0,
                'invalid': 0,
                'by_type': {}
            }