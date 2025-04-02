"""
Intelligent Document Processing System
Document model
"""

from datetime import datetime
import json
from app import db


class Document(db.Model):
    """Document model for storing document metadata and extracted information"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_path = db.Column(db.String(500), nullable=False)
    processed_path = db.Column(db.String(500), nullable=True)
    document_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='uploaded')  # uploaded, processing, completed, failed
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed_date = db.Column(db.DateTime, nullable=True)
    
    # Extracted data stored as JSON
    extracted_data = db.Column(db.Text, nullable=True)
    
    # Document validation and confidence
    is_valid = db.Column(db.Boolean, default=False)
    confidence_score = db.Column(db.Float, default=0.0)
    
    # Relationships
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    exceptions = db.relationship('Exception', backref='document', lazy='dynamic')
    
    def __init__(self, filename, original_path, document_type):
        self.filename = filename
        self.original_path = original_path
        self.document_type = document_type
    
    def update_status(self, status):
        """Update document status"""
        self.status = status
        if status == 'completed':
            self.processed_date = datetime.utcnow()
        db.session.commit()
    
    def add_extracted_data(self, data):
        """Add or update extracted data"""
        self.extracted_data = json.dumps(data)
        db.session.commit()
    
    def get_extracted_data(self):
        """Get extracted data as Python dictionary"""
        if self.extracted_data:
            return json.loads(self.extracted_data)
        return {}
    
    def mark_as_valid(self, confidence_score=1.0):
        """Mark document as valid with confidence score"""
        self.is_valid = True
        self.confidence_score = confidence_score
        db.session.commit()
    
    def mark_as_invalid(self, confidence_score=0.0):
        """Mark document as invalid with confidence score"""
        self.is_valid = False
        self.confidence_score = confidence_score
        db.session.commit()
    
    def to_dict(self):
        """Convert document to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'document_type': self.document_type,
            'status': self.status,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'extracted_data': self.get_extracted_data(),
            'is_valid': self.is_valid,
            'confidence_score': self.confidence_score,
            'batch_id': self.batch_id
        }
    
    def __repr__(self):
        return f'<Document {self.id}: {self.filename}>'