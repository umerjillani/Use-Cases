"""
Intelligent Document Processing System
Main API routes
"""

import os
import json
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models.document import Document
from app.models.batch import Batch
from app.processing.document_processor import DocumentProcessor

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@api_bp.route('/status', methods=['GET'])
def status():
    """API status check"""
    return jsonify({
        'status': 'online',
        'version': '1.0.0',
        'name': 'Intelligent Document Processing System'
    })


@api_bp.route('/upload', methods=['POST'])
def upload_document():
    """
    Upload document endpoint
    
    Request:
        - file: Document file
        - document_type: Type of document (claim, agency_services, cancellation, mortgage_change, payment, auto)
        
    Response:
        - success: Boolean indicating if upload was successful
        - document_id: ID of uploaded document
        - message: Status message
    """
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file part in the request'
            }), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # Check if file is allowed
        if not file or not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'File type not allowed'
            }), 400
        
        # Get document type
        document_type = request.form.get('document_type', 'auto')
        
        # Get upload folder path
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        # Secure filename and save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        
        # If file already exists, add timestamp to filename
        if os.path.exists(file_path):
            name, ext = os.path.splitext(filename)
            timestamp = int(datetime.now().timestamp())
            filename = f"{name}_{timestamp}{ext}"
            file_path = os.path.join(upload_folder, filename)
        
        file.save(file_path)
        
        # Create document record
        document = Document(
            filename=filename,
            original_path=file_path,
            document_type=document_type
        )
        
        db.session.add(document)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'document_id': document.id,
            'message': 'Document uploaded successfully'
        })
    
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error uploading document: {str(e)}"
        }), 500


@api_bp.route('/process/<int:document_id>', methods=['POST'])
def process_document(document_id):
    """
    Process document endpoint
    
    Request:
        - document_id: ID of document to process
        
    Response:
        - success: Boolean indicating if processing was successful
        - document: Processed document data
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
        
        # Create document processor with app context
        processor = DocumentProcessor(current_app)
        
        # Process document
        result = processor.process_document(document_id)
        
        if result:
            # Get updated document
            document = Document.query.get(document_id)
            
            return jsonify({
                'success': True,
                'document': document.to_dict(),
                'message': 'Document processed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Document processing failed'
            }), 500
    
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error processing document: {str(e)}"
        }), 500


@api_bp.route('/export/batch/<int:batch_id>', methods=['POST'])
def export_batch(batch_id):
    """
    Export batch endpoint
    
    Request:
        - batch_id: ID of batch to export
        - format: Export format (json, xml)
        
    Response:
        - success: Boolean indicating if export was successful
        - export_path: Path to exported file
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
        
        # Get export format
        export_format = request.json.get('format', 'json')
        if export_format not in ['json', 'xml']:
            return jsonify({
                'success': False,
                'message': f"Unsupported export format: {export_format}"
            }), 400
        
        # Get export folder path
        export_folder = current_app.config['EXPORTED_FOLDER']
        
        # Create export filename
        export_filename = f"batch_{batch_id}_{int(datetime.now().timestamp())}.{export_format}"
        export_path = os.path.join(export_folder, export_filename)
        
        # Export batch data
        export_data = {
            'batch_id': batch.id,
            'batch_name': batch.name,
            'batch_status': batch.status,
            'creation_date': batch.creation_date.isoformat() if batch.creation_date else None,
            'total_amount': batch.total_amount,
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
        
        # Write export file
        if export_format == 'json':
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
        else:  # xml format
            # Simple XML conversion (in a real system, use a proper XML library)
            with open(export_path, 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<Batch>\n')
                f.write(f'  <BatchId>{batch.id}</BatchId>\n')
                f.write(f'  <BatchName>{batch.name}</BatchName>\n')
                f.write(f'  <BatchStatus>{batch.status}</BatchStatus>\n')
                f.write(f'  <CreationDate>{batch.creation_date.isoformat() if batch.creation_date else ""}</CreationDate>\n')
                f.write(f'  <TotalAmount>{batch.total_amount}</TotalAmount>\n')
                f.write('  <Documents>\n')
                
                for document in batch.documents:
                    f.write('    <Document>\n')
                    f.write(f'      <DocumentId>{document.id}</DocumentId>\n')
                    f.write(f'      <Filename>{document.filename}</Filename>\n')
                    f.write(f'      <DocumentType>{document.document_type}</DocumentType>\n')
                    f.write('      <ExtractedData>\n')
                    
                    extracted_data = document.get_extracted_data()
                    for key, value in extracted_data.items():
                        f.write(f'        <{key}>{value}</{key}>\n')
                    
                    f.write('      </ExtractedData>\n')
                    f.write(f'      <IsValid>{str(document.is_valid).lower()}</IsValid>\n')
                    f.write(f'      <ConfidenceScore>{document.confidence_score}</ConfidenceScore>\n')
                    f.write('    </Document>\n')
                
                f.write('  </Documents>\n')
                f.write('</Batch>\n')
        
        # Update batch export path and status
        batch.export_batch(export_path)
        
        return jsonify({
            'success': True,
            'export_path': export_path,
            'message': f"Batch exported successfully in {export_format} format"
        })
    
    except Exception as e:
        logger.error(f"Error exporting batch: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error exporting batch: {str(e)}"
        }), 500


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get system statistics
    
    Response:
        - total_documents: Total number of documents
        - processed_documents: Number of processed documents
        - failed_documents: Number of failed documents
        - total_batches: Total number of batches
        - exported_batches: Number of exported batches
        - total_exceptions: Total number of exceptions
        - open_exceptions: Number of open exceptions
    """
    try:
        from app.models.exception import Exception as DocException
        
        # Calculate statistics
        total_documents = Document.query.count()
        processed_documents = Document.query.filter(Document.status == 'completed').count()
        failed_documents = Document.query.filter(Document.status == 'failed').count()
        
        total_batches = Batch.query.count()
        exported_batches = Batch.query.filter(Batch.status == 'exported').count()
        
        total_exceptions = DocException.query.count()
        open_exceptions = DocException.query.filter(DocException.status == 'open').count()
        
        return jsonify({
            'total_documents': total_documents,
            'processed_documents': processed_documents,
            'failed_documents': failed_documents,
            'total_batches': total_batches,
            'exported_batches': exported_batches,
            'total_exceptions': total_exceptions,
            'open_exceptions': open_exceptions
        })
    
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error getting statistics: {str(e)}"
        }), 500