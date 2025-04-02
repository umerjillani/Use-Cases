"""
Intelligent Document Processing System
Batch model
"""

from datetime import datetime
import json
import os
from app import db


class Batch(db.Model):
    """Batch model for grouping documents for processing and export"""
    __tablename__ = 'batches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='created')  # created, processing, validated, exported, failed
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    completed_date = db.Column(db.DateTime, nullable=True)
    export_date = db.Column(db.DateTime, nullable=True)
    export_path = db.Column(db.String(500), nullable=True)
    
    # Total amounts for reconciliation
    total_amount = db.Column(db.Float, default=0.0)
    verified_amount = db.Column(db.Float, default=0.0)
    
    # Batch metadata stored as JSON
    # Batch metadata stored as JSON
    batch_metadata = db.Column(db.Text, nullable=True)
    
    # Relationships
    documents = db.relationship('Document', backref='batch', lazy='dynamic')
    exceptions = db.relationship('Exception', backref='batch', lazy='dynamic')
    
    def __init__(self, name):
        self.name = name
    
    def update_status(self, status):
        """Update batch status"""
        self.status = status
        if status == 'validated':
            self.completed_date = datetime.utcnow()
        elif status == 'exported':
            self.export_date = datetime.utcnow()
        db.session.commit()
    
    def add_document(self, document):
        """Add document to batch"""
        document.batch_id = self.id
        db.session.commit()
        
        # Update totals if document has amount
        extracted_data = document.get_extracted_data()
        if 'amount' in extracted_data:
            try:
                amount = float(extracted_data['amount'])
                self.total_amount += amount
                db.session.commit()
            except (ValueError, TypeError):
                pass
    
    def remove_document(self, document):
        """Remove document from batch"""
        # Update totals if document has amount
        extracted_data = document.get_extracted_data()
        if 'amount' in extracted_data:
            try:
                amount = float(extracted_data['amount'])
                self.total_amount -= amount
            except (ValueError, TypeError):
                pass
        
        document.batch_id = None
        db.session.commit()
    
    def verify_amounts(self):
        """Verify total amounts against verified amount"""
        return abs(self.total_amount - self.verified_amount) < 0.01
    
    def set_verified_amount(self, amount):
        """Set the verified amount for reconciliation"""
        self.verified_amount = float(amount)
        db.session.commit()
    
    def export_batch(self, export_path):
        """Mark batch as exported with export path"""
        self.export_path = export_path
        self.update_status('exported')
    
    def get_metadata(self):
        """Get metadata as Python dictionary"""
        if self.batch_metadata:
            return json.loads(self.batch_metadata)
        return {}
    
    def set_metadata(self, data):
        """Set batch metadata"""
        self.batch_metadata = json.dumps(data)
        db.session.commit()
    
    def get_document_count(self):
        """Get count of documents in batch"""
        return self.documents.count()
    
    def get_exception_count(self):
        """Get count of exceptions in batch"""
        return self.exceptions.count()
    
    def to_dict(self):
        """Convert batch to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'export_date': self.export_date.isoformat() if self.export_date else None,
            'total_amount': self.total_amount,
            'verified_amount': self.verified_amount,
            'document_count': self.get_document_count(),
            'exception_count': self.get_exception_count(),
            'metadata': self.get_metadata()
        }
    
    def __repr__(self):
        return f'<Batch {self.id}: {self.name}>'