"""
Intelligent Document Processing System
Exception handling logic
"""

import logging
from datetime import datetime

from app import db
from app.models.exception import Exception as DocException
from app.models.document import Document
from app.models.batch import Batch

# Configure logging
logger = logging.getLogger(__name__)


class ExceptionService:
    """Service class for exception operations"""
    
    @staticmethod
    def create_exception(exception_type, message, document_id, field_name=None, severity='warning', details=None):
        """
        Create a new exception
        
        Args:
            exception_type: Type of exception
            message: Exception message
            document_id: Document ID
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
            logger.error(f"Error creating exception: {str(e)}", exc_info=True)
            return None, f"Error creating exception: {str(e)}"
    
    @staticmethod
    def get_exception(exception_id):
        """
        Get exception by ID
        
        Args:
            exception_id: Exception ID
            
        Returns:
            Exception: Exception object
        """
        return DocException.query.get(exception_id)
    
    @staticmethod
    def get_exceptions(filters=None, limit=None, offset=None):
        """
        Get exceptions with optional filtering and pagination
        
        Args:
            filters: Dictionary of filter criteria
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            tuple: (exceptions, total_count)
        """
        try:
            # Start with base query
            query = DocException.query
            
            # Apply filters
            if filters:
                if 'status' in filters:
                    query = query.filter(DocException.status == filters['status'])
                
                if 'severity' in filters:
                    query = query.filter(DocException.severity == filters['severity'])
                
                if 'document_id' in filters:
                    query = query.filter(DocException.document_id == filters['document_id'])
                
                if 'batch_id' in filters:
                    query = query.filter(DocException.batch_id == filters['batch_id'])
                
                if 'exception_type' in filters:
                    query = query.filter(DocException.exception_type == filters['exception_type'])
            
            # Get total count
            total_count = query.count()
            
            # Apply sorting
            query = query.order_by(DocException.created_date.desc())
            
            # Apply pagination
            if limit is not None:
                query = query.limit(limit)
            
            if offset is not None:
                query = query.offset(offset)
            
            # Execute query
            exceptions = query.all()
            
            return exceptions, total_count
        
        except Exception as e:
            logger.error(f"Error getting exceptions: {str(e)}", exc_info=True)
            return [], 0
    
    @staticmethod
    def update_exception_status(exception_id, status):
        """
        Update exception status
        
        Args:
            exception_id: Exception ID
            status: New status
            
        Returns:
            tuple: (exception, message)
        """
        try:
            # Get exception
            exception = DocException.query.get(exception_id)
            if not exception:
                return None, f"Exception with ID {exception_id} not found"
            
            # Validate status
            valid_statuses = ['open', 'in_progress', 'resolved']
            if status not in valid_statuses:
                return None, f"Invalid status: {status}. Must be one of {', '.join(valid_statuses)}"
            
            # Update status
            exception.update_status(status)
            
            return exception, f"Exception status updated to {status}"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating exception status: {str(e)}", exc_info=True)
            return None, f"Error updating exception status: {str(e)}"
    
    @staticmethod
    def delete_exception(exception_id):
        """
        Delete exception
        
        Args:
            exception_id: Exception ID
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Get exception
            exception = DocException.query.get(exception_id)
            if not exception:
                return False, f"Exception with ID {exception_id} not found"
            
            # Delete exception
            db.session.delete(exception)
            db.session.commit()
            
            return True, "Exception deleted successfully"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting exception: {str(e)}", exc_info=True)
            return False, f"Error deleting exception: {str(e)}"
    
    @staticmethod
    def resolve_all_exceptions(filters=None):
        """
        Resolve all exceptions matching filters
        
        Args:
            filters: Dictionary of filter criteria
            
        Returns:
            tuple: (count, message)
        """
        try:
            # Start with base query for open exceptions
            query = DocException.query.filter(DocException.status != 'resolved')
            
            # Apply filters
            if filters:
                if 'document_id' in filters:
                    query = query.filter(DocException.document_id == filters['document_id'])
                
                if 'batch_id' in filters:
                    query = query.filter(DocException.batch_id == filters['batch_id'])
                
                if 'severity' in filters:
                    query = query.filter(DocException.severity == filters['severity'])
                
                if 'exception_type' in filters:
                    query = query.filter(DocException.exception_type == filters['exception_type'])
            
            # Get exceptions
            exceptions = query.all()
            
            # Update status for each exception
            count = 0
            for exception in exceptions:
                exception.update_status('resolved')
                count += 1
            
            return count, f"Resolved {count} exceptions"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resolving exceptions: {str(e)}", exc_info=True)
            return 0, f"Error resolving exceptions: {str(e)}"
    
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
    def get_batch_exceptions(batch_id):
        """
        Get exceptions for batch
        
        Args:
            batch_id: Batch ID
            
        Returns:
            list: List of exceptions
        """
        try:
            return DocException.query.filter_by(batch_id=batch_id).order_by(DocException.created_date.desc()).all()
        
        except Exception as e:
            logger.error(f"Error getting batch exceptions: {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    def get_exception_stats():
        """
        Get exception statistics
        
        Returns:
            dict: Dictionary with exception statistics
        """
        try:
            total = DocException.query.count()
            
            by_status = {}
            for status in ['open', 'in_progress', 'resolved']:
                count = DocException.query.filter(DocException.status == status).count()
                if count > 0:
                    by_status[status] = count
            
            by_severity = {}
            for severity in ['info', 'warning', 'error']:
                count = DocException.query.filter(DocException.severity == severity).count()
                if count > 0:
                    by_severity[severity] = count
            
            by_type = {}
            exception_types = db.session.query(DocException.exception_type, 
                                              db.func.count(DocException.id))\
                                      .group_by(DocException.exception_type)\
                                      .all()
            
            for exc_type, count in exception_types:
                if count > 0:
                    by_type[exc_type] = count
            
            return {
                'total': total,
                'by_status': by_status,
                'by_severity': by_severity,
                'by_type': by_type
            }
        
        except Exception as e:
            logger.error(f"Error getting exception stats: {str(e)}", exc_info=True)
            return {
                'total': 0,
                'by_status': {},
                'by_severity': {},
                'by_type': {}
            }
    
    @staticmethod
    def create_system_exception(message, details=None):
        """
        Create a system exception (not tied to a specific document)
        
        Args:
            message: Exception message
            details: Additional details (optional)
            
        Returns:
            None (logs the exception but doesn't store in database)
        """
        try:
            # Log the exception
            logger.error(f"System exception: {message}")
            
            if details:
                logger.error(f"Exception details: {details}")
        
        except Exception as e:
            logger.error(f"Error creating system exception: {str(e)}", exc_info=True)