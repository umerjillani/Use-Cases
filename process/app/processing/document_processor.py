"""
Intelligent Document Processing System
Main document processing logic
"""

import os
import logging
import shutil
from datetime import datetime
import tempfile
import pytesseract
from pdf2image import convert_from_path

from app import db
from app.models.document import Document
from app.models.exception import Exception as DocException
from app.processing.extractors.text_extractor import extract_text_from_image
from app.processing.extractors.policy_extractor import extract_policy_number
from app.processing.extractors.amount_extractor import extract_amount
from app.processing.extractors.date_extractor import extract_dates
from app.processing.extractors.name_extractor import extract_names
from app.processing.extractors.claim_extractor import extract_claim_number
from app.processing.extractors.loan_extractor import extract_loan_number
from app.processing.classifiers.document_classifier import classify_document
from app.processing.validators.document_validator import validate_document

# Configure logging
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Document processor class for handling document processing logic"""
    
    def __init__(self, app=None):
        self.app = app
        self.config = app.config if app else {}
    
    def process_document(self, document_id):
        """
        Process a document by ID
        
        Args:
            document_id: The ID of the document to process
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        document = Document.query.get(document_id)
        if not document:
            logger.error(f"Document with ID {document_id} not found")
            return False
        
        try:
            # Update document status
            document.update_status('processing')
            
            # Extract text from document
            extracted_text, page_texts = self._extract_text_from_pdf(document.original_path)
            
            # Skip processing if no text was extracted
            if not extracted_text:
                self._create_exception(document.id, "text_extraction_failed", 
                                      "Failed to extract text from document", 
                                      severity="error")
                document.update_status('failed')
                return False
            
            # Auto-classify document if type is not specified
            if document.document_type == 'auto' or not document.document_type:
                detected_type = classify_document(extracted_text)
                document.document_type = detected_type
                db.session.commit()
            
            # Extract information based on document type
            extracted_data = self._extract_information(document.document_type, extracted_text, page_texts)
            
            # Add extracted data to document
            document.add_extracted_data(extracted_data)
            
            # Validate extracted data
            validation_result = validate_document(document.document_type, extracted_data)
            
            if validation_result['is_valid']:
                document.mark_as_valid(validation_result['confidence'])
                document.update_status('completed')
                
                # Move to processed folder
                self._move_to_processed(document)
            else:
                document.mark_as_invalid(validation_result['confidence'])
                
                # Create exceptions for validation issues
                for issue in validation_result['issues']:
                    self._create_exception(document.id, "validation_failed", 
                                          issue['message'], 
                                          field_name=issue['field'],
                                          severity=issue['severity'])
                
                document.update_status('completed')
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
            document.update_status('failed')
            self._create_exception(document.id, "processing_error", 
                                  f"Error processing document: {str(e)}", 
                                  severity="error")
            return False
    
    def _extract_text_from_pdf(self, pdf_path):
        """
        Extract text from PDF file using OCR
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            tuple: (full_text, page_texts) where full_text is the combined text and 
                  page_texts is a list of texts for each page
        """
        try:
            # Create temporary directory for images
            with tempfile.TemporaryDirectory() as temp_dir:
                # Convert PDF to images
                pages = convert_from_path(pdf_path, 300)
                
                page_texts = []
                for i, page in enumerate(pages):
                    # Save page as image
                    image_path = os.path.join(temp_dir, f'page_{i+1}.png')
                    page.save(image_path, 'PNG')
                    
                    # Extract text from image
                    text = extract_text_from_image(image_path)
                    page_texts.append(text)
                
                # Combine all page texts
                full_text = "\n\n".join(page_texts)
                
                return full_text, page_texts
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}", exc_info=True)
            return None, []
    
    def _extract_information(self, document_type, full_text, page_texts):
        """
        Extract information based on document type
        
        Args:
            document_type: Type of document
            full_text: Full text extracted from document
            page_texts: List of texts for each page
            
        Returns:
            dict: Extracted information
        """
        extracted_data = {}
        
        # Common fields for all document types
        extracted_data['policy_number'] = extract_policy_number(full_text)
        extracted_data['dates'] = extract_dates(full_text)
        
        # Document type specific extraction
        if document_type == 'claim':
            extracted_data['claim_number'] = extract_claim_number(full_text)
            extracted_data['amount'] = extract_amount(full_text)
            extracted_data['claimant_name'] = extract_names(full_text)
        
        elif document_type == 'agency_services':
            extracted_data['agent_name'] = extract_names(full_text)
            extracted_data['amount'] = extract_amount(full_text)
        
        elif document_type == 'cancellation':
            extracted_data['cancellation_reason'] = self._extract_cancellation_reason(full_text)
            extracted_data['effective_date'] = self._extract_effective_date(extracted_data['dates'])
        
        elif document_type == 'mortgage_change':
            extracted_data['loan_number'] = extract_loan_number(full_text)
            extracted_data['mortgagee_name'] = extract_names(full_text, name_type='business')
            extracted_data['property_address'] = self._extract_property_address(full_text)
        
        elif document_type == 'payment':
            extracted_data['amount'] = extract_amount(full_text)
            extracted_data['payment_method'] = self._extract_payment_method(full_text)
            extracted_data['payer_name'] = extract_names(full_text)
        
        return extracted_data
    
    def _extract_cancellation_reason(self, text):
        """Extract cancellation reason from text"""
        # Implementation depends on document format
        # This is a simplified version
        if 'non-payment' in text.lower():
            return 'non-payment'
        elif 'request' in text.lower() and 'insured' in text.lower():
            return 'insured-request'
        elif 'underwriting' in text.lower():
            return 'underwriting'
        return 'other'
    
    def _extract_effective_date(self, dates):
        """Extract effective date from list of dates"""
        # Implementation depends on document format
        # This is a simplified version
        if not dates:
            return None
        
        # Try to find date labeled as effective
        for date in dates:
            if 'effective' in date.get('label', '').lower():
                return date.get('date')
        
        # Default to the latest date
        dates_only = [d.get('date') for d in dates if d.get('date')]
        if dates_only:
            dates_only.sort()
            return dates_only[-1]
        
        return None
    
    def _extract_property_address(self, text):
        """Extract property address from text"""
        # Implementation depends on document format
        # This is a simplified placeholder
        # In a real system, would use NER or regex patterns to extract address
        return "Address extraction not implemented"
    
    def _extract_payment_method(self, text):
        """Extract payment method from text"""
        text_lower = text.lower()
        if 'check' in text_lower or 'cheque' in text_lower:
            return 'check'
        elif 'credit' in text_lower or 'card' in text_lower:
            return 'credit_card'
        elif 'ach' in text_lower or 'direct deposit' in text_lower:
            return 'ach'
        elif 'wire' in text_lower:
            return 'wire'
        return 'unknown'
    
    def _move_to_processed(self, document):
        """
        Move document to processed folder
        
        Args:
            document: Document object
        """
        if not self.app:
            logger.warning("App context not available, cannot move document")
            return
        
        processed_folder = self.app.config.get('PROCESSED_FOLDER')
        if not processed_folder:
            logger.warning("Processed folder not configured")
            return
        
        # Create processed path
        filename = os.path.basename(document.original_path)
        processed_path = os.path.join(processed_folder, filename)
        
        # Copy file to processed folder
        try:
            shutil.copy2(document.original_path, processed_path)
            document.processed_path = processed_path
            db.session.commit()
        except Exception as e:
            logger.error(f"Error moving document to processed folder: {str(e)}", exc_info=True)
    
    def _create_exception(self, document_id, exception_type, message, field_name=None, severity='warning', details=None):
        """
        Create an exception record
        
        Args:
            document_id: Document ID
            exception_type: Type of exception
            message: Exception message
            field_name: Name of field with issue (optional)
            severity: Exception severity (info, warning, error)
            details: Additional details (optional)
        """
        try:
            exception = DocException(
                exception_type=exception_type,
                message=message,
                document_id=document_id,
                field_name=field_name,
                severity=severity
            )
            
            if details:
                exception.set_details(details)
            
            db.session.add(exception)
            db.session.commit()
            
            logger.info(f"Created exception {exception.id} for document {document_id}: {message}")
        except Exception as e:
            logger.error(f"Error creating exception: {str(e)}", exc_info=True)