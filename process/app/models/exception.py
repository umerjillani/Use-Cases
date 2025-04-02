"""
Intelligent Document Processing System
Exception model
"""

from datetime import datetime
import json
from app import db


class Exception(db.Model):
    """Exception model for tracking document processing exceptions"""
    __tablename__ = 'exceptions'
    
    id = db.Column(db.Integer, primary_key=True)
    exception_type = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    field_name = db.Column(db.String(100), nullable=True)
    severity = db.Column(db.String(20), default='warning')  # info, warning, error
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_date = db.Column(db.DateTime, nullable=True)
    
    # Exception details stored as JSON
    details = db.Column(db.Text, nullable=True)
    
    # Relationships
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'))
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    
    def __init__(self, exception_type, message, document_id, field_name=None, severity='warning', details=None):
        self.exception_type = exception_type
        self.message = message
        self.document_id = document_id
        self.field_name = field_name
        self.severity = severity
        
        if details:
            self.set_details(details)
        
        # Get batch_id from document if available
        from app.models.document import Document
        document = Document.query.get(document_id)
        if document and document.batch_id:
            self.batch_id = document.batch_id
    
    def update_status(self, status):
        """Update exception status"""
        self.status = status
        if status == 'resolved':
            self.resolved_date = datetime.utcnow()
        db.session.commit()
    
    def set_details(self, details):
        """Set exception details"""
        self.details = json.dumps(details)
        db.session.commit()
    
    def get_details(self):
        """Get exception details as Python dictionary"""
        if self.details:
            return json.loads(self.details)
        return {}
    
    def to_dict(self):
        """Convert exception to dictionary"""
        return {
            'id': self.id,
            'exception_type': self.exception_type,
            'message': self.message,
            'field_name': self.field_name,
            'severity': self.severity,
            'status': self.status,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'resolved_date': self.resolved_date.isoformat() if self.resolved_date else None,
            'document_id': self.document_id,
            'batch_id': self.batch_id,
            'details': self.get_details()
        }
    
    def __repr__(self):
        return f'<Exception {self.id}: {self.exception_type}>'