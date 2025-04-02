"""
Intelligent Document Processing System
Batch business logic
"""

import os
import json
import logging
from datetime import datetime
from flask import current_app

from app import db
from app.models.batch import Batch
from app.models.document import Document
from app.models.exception import Exception as DocException
from app.utils.file_utils import create_zip_archive, upload_to_ftp
from app.utils.helpers import to_json, to_xml, generate_batch_name

# Configure logging
logger = logging.getLogger(__name__)


class BatchService:
    """Service class for batch operations"""
    
    @staticmethod
    def create_batch(name=None, document_ids=None):
        """
        Create a new batch
        
        Args:
            name: Batch name (optional)
            document_ids: List of document IDs to add to batch (optional)
            
        Returns:
            tuple: (batch, message)
        """
        try:
            # Generate name if not provided
            if not name:
                name = generate_batch_name()
            
            # Create batch
            batch = Batch(name=name)
            db.session.add(batch)
            db.session.commit()
            
            # Add documents if provided
            if document_ids:
                for document_id in document_ids:
                    document = Document.query.get(document_id)
                    if document:
                        batch.add_document(document)
            
            return batch, "Batch created successfully"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating batch: {str(e)}", exc_info=True)
            return None, f"Error creating batch: {str(e)}"
    
    @staticmethod
    def get_batch(batch_id):
        """
        Get batch by ID
        
        Args:
            batch_id: Batch ID
            
        Returns:
            Batch: Batch object
        """
        return Batch.query.get(batch_id)
    
    @staticmethod
    def get_batches(filters=None, limit=None, offset=None):
        """
        Get batches with optional filtering and pagination
        
        Args:
            filters: Dictionary of filter criteria
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            tuple: (batches, total_count)
        """
        try:
            # Start with base query
            query = Batch.query
            
            # Apply filters
            if filters:
                if 'status' in filters:
                    query = query.filter(Batch.status == filters['status'])
                
                if 'name' in filters:
                    query = query.filter(Batch.name.ilike(f"%{filters['name']}%"))
            
            # Get total count
            total_count = query.count()
            
            # Apply sorting
            query = query.order_by(Batch.creation_date.desc())
            
            # Apply pagination
            if limit is not None:
                query = query.limit(limit)
            
            if offset is not None:
                query = query.offset(offset)
            
            # Execute query
            batches = query.all()
            
            return batches, total_count
        
        except Exception as e:
            logger.error(f"Error getting batches: {str(e)}", exc_info=True)
            return [], 0
    
    @staticmethod
    def update_batch(batch_id, data):
        """
        Update batch
        
        Args:
            batch_id: Batch ID
            data: Dictionary with batch data
            
        Returns:
            tuple: (batch, message)
        """
        try:
            # Get batch
            batch = Batch.query.get(batch_id)
            if not batch:
                return None, f"Batch with ID {batch_id} not found"
            
            # Update batch fields
            if 'name' in data:
                batch.name = data['name']
            
            if 'status' in data:
                batch.update_status(data['status'])
            
            if 'verified_amount' in data:
                batch.set_verified_amount(data['verified_amount'])
            
            if 'metadata' in data:
                batch.set_metadata(data['metadata'])
            
            db.session.commit()
            
            return batch, "Batch updated successfully"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating batch: {str(e)}", exc_info=True)
            return None, f"Error updating batch: {str(e)}"
    
    @staticmethod
    def delete_batch(batch_id, delete_documents=False):
        """
        Delete batch
        
        Args:
            batch_id: Batch ID
            delete_documents: Whether to delete the documents in the batch
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Get batch
            batch = Batch.query.get(batch_id)
            if not batch:
                return False, f"Batch with ID {batch_id} not found"
            
            if delete_documents:
                # Get documents in batch
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
            
            # Delete batch exceptions
            DocException.query.filter_by(batch_id=batch_id).delete()
            
            # Delete batch
            db.session.delete(batch)
            db.session.commit()
            
            return True, f"Batch deleted successfully{' with all documents' if delete_documents else ''}"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting batch: {str(e)}", exc_info=True)
            return False, f"Error deleting batch: {str(e)}"
    
    @staticmethod
    def add_documents_to_batch(batch_id, document_ids):
        """
        Add documents to batch
        
        Args:
            batch_id: Batch ID
            document_ids: List of document IDs
            
        Returns:
            tuple: (batch, count, message)
        """
        try:
            # Get batch
            batch = Batch.query.get(batch_id)
            if not batch:
                return None, 0, f"Batch with ID {batch_id} not found"
            
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
            
            return batch, added_count, f"Added {added_count} documents to batch"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding documents to batch: {str(e)}", exc_info=True)
            return None, 0, f"Error adding documents to batch: {str(e)}"
    
    @staticmethod
    def remove_document_from_batch(batch_id, document_id):
        """
        Remove document from batch
        
        Args:
            batch_id: Batch ID
            document_id: Document ID
            
        Returns:
            tuple: (batch, message)
        """
        try:
            # Get batch
            batch = Batch.query.get(batch_id)
            if not batch:
                return None, f"Batch with ID {batch_id} not found"
            
            # Get document
            document = Document.query.get(document_id)
            if not document:
                return None, f"Document with ID {document_id} not found"
            
            # Check if document is in batch
            if document.batch_id != batch_id:
                return None, f"Document with ID {document_id} is not in batch with ID {batch_id}"
            
            # Remove document from batch
            batch.remove_document(document)
            
            return batch, f"Document removed from batch"
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error removing document from batch: {str(e)}", exc_info=True)
            return None, f"Error removing document from batch: {str(e)}"
    
    @staticmethod
    def validate_batch(batch_id, verified_amount=None):
        """
        Validate batch
        
        Args:
            batch_id: Batch ID
            verified_amount: Optional verified amount for validation
            
        Returns:
            tuple: (is_valid, issues, message)
        """
        try:
            # Get batch
            batch = Batch.query.get(batch_id)
            if not batch:
                return False, [], f"Batch with ID {batch_id} not found"
            
            # Set verified amount if provided
            if verified_amount is not None:
                batch.set_verified_amount(verified_amount)
            
            # Initialize validation issues
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
            
            return is_valid, issues, 'Batch validation complete'
        
        except Exception as e:
            logger.error(f"Error validating batch: {str(e)}", exc_info=True)
            return False, [], f"Error validating batch: {str(e)}"
    
    @staticmethod
    def export_batch(batch_id, export_format='json'):
        """
        Export batch data
        
        Args:
            batch_id: Batch ID
            export_format: Export format ('json' or 'xml')
            
        Returns:
            tuple: (file_path, message)
        """
        try:
            # Get batch
            batch = Batch.query.get(batch_id)
            if not batch:
                return None, f"Batch with ID {batch_id} not found"
            
            # Prepare export data
            export_data = {
                'batch_id': batch.id,
                'batch_name': batch.name,
                'batch_status': batch.status,
                'creation_date': batch.creation_date.isoformat() if batch.creation_date else None,
                'export_date': datetime.utcnow().isoformat(),
                'total_amount': batch.total_amount,
                'verified_amount': batch.verified_amount,
                'documents': []
            }
            
            # Add documents to export data
            for document in batch.documents:
                export_data['documents'].append({
                    'document_id': document.id,
                    'filename': document.filename,
                    'document_type': document.document_type,
                    'extracted_data': document.get_extracted_data(),
                    'is_valid': document.is_valid,
                    'confidence_score': document.confidence_score
                })
            
            # Get export folder path
            export_folder = current_app.config['EXPORTED_FOLDER']
            
            # Create export filename
            timestamp = int(datetime.now().timestamp())
            export_filename = f"batch_{batch_id}_{timestamp}.{export_format}"
            export_path = os.path.join(export_folder, export_filename)
            
            # Create export directory if it doesn't exist
            os.makedirs(export_folder, exist_ok=True)
            
            # Write export file
            if export_format == 'json':
                with open(export_path, 'w') as f:
                    f.write(to_json(export_data, pretty=True))
            else:  # xml format
                with open(export_path, 'w') as f:
                    f.write(to_xml(export_data, root_name='Batch'))
            
            # Update batch export path and status
            batch.export_batch(export_path)
            
            return export_path, f"Batch exported successfully in {export_format} format"
        
        except Exception as e:
            logger.error(f"Error exporting batch: {str(e)}", exc_info=True)
            return None, f"Error exporting batch: {str(e)}"
    
    @staticmethod
    def upload_batch_to_ftp(batch_id, export_format='json'):
        """
        Export batch data and upload to FTP
        
        Args:
            batch_id: Batch ID
            export_format: Export format ('json' or 'xml')
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Export batch
            export_path, message = BatchService.export_batch(batch_id, export_format)
            if not export_path:
                return False, message
            
            # Get FTP settings from config
            ftp_host = current_app.config['FTP_HOST']
            ftp_user = current_app.config['FTP_USER']
            ftp_pass = current_app.config['FTP_PASS']
            ftp_dir = current_app.config['FTP_DIR']
            
            # Upload to FTP
            success = upload_to_ftp(
                export_path, 
                ftp_host, 
                ftp_user, 
                ftp_pass, 
                ftp_dir
            )
            
            if success:
                # Update batch status
                batch = Batch.query.get(batch_id)
                batch.update_status('exported')
                
                return True, "Batch exported and uploaded to FTP successfully"
            else:
                return False, "Failed to upload batch to FTP"
        
        except Exception as e:
            logger.error(f"Error uploading batch to FTP: {str(e)}", exc_info=True)
            return False, f"Error uploading batch to FTP: {str(e)}"
    
    @staticmethod
    def create_batch_export_archive(batch_id):
        """
        Create ZIP archive with batch export and document files
        
        Args:
            batch_id: Batch ID
            
        Returns:
            tuple: (archive_path, message)
        """
        try:
            # Get batch
            batch = Batch.query.get(batch_id)
            if not batch:
                return None, f"Batch with ID {batch_id} not found"
            
            # Export batch to JSON
            export_path, message = BatchService.export_batch(batch_id, 'json')
            if not export_path:
                return None, message
            
            # Get document files
            files = [export_path]
            for document in batch.documents:
                if document.original_path and os.path.exists(document.original_path):
                    files.append(document.original_path)
            
            # Create archive filename
            export_folder = current_app.config['EXPORTED_FOLDER']
            timestamp = int(datetime.now().timestamp())
            archive_filename = f"batch_{batch_id}_{timestamp}.zip"
            archive_path = os.path.join(export_folder, archive_filename)
            
            # Create ZIP archive
            create_zip_archive(files, archive_path)
            
            return archive_path, "Batch export archive created successfully"
        
        except Exception as e:
            logger.error(f"Error creating batch export archive: {str(e)}", exc_info=True)
            return None, f"Error creating batch export archive: {str(e)}"
    
    @staticmethod
    def get_batch_stats():
        """
        Get batch statistics
        
        Returns:
            dict: Dictionary with batch statistics
        """
        try:
            total = Batch.query.count()
            
            by_status = {}
            for status in ['created', 'processing', 'validated', 'exported', 'failed']:
                count = Batch.query.filter(Batch.status == status).count()
                if count > 0:
                    by_status[status] = count
            
            total_documents = Document.query.filter(Document.batch_id != None).count()
            total_amount = db.session.query(db.func.sum(Batch.total_amount)).scalar() or 0
            
            return {
                'total': total,
                'by_status': by_status,
                'total_documents': total_documents,
                'total_amount': total_amount
            }
        
        except Exception as e:
            logger.error(f"Error getting batch stats: {str(e)}", exc_info=True)
            return {
                'total': 0,
                'by_status': {},
                'total_documents': 0,
                'total_amount': 0
            }