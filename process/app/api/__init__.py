"""
Intelligent Document Processing System
API module initialization
"""

# Import API routes
from app.api.routes import api_bp
from app.api.document_routes import document_bp
from app.api.batch_routes import batch_bp
from app.api.exception_routes import exception_bp
from app.api.dashboard_routes import dashboard_bp

# Export blueprints
__all__ = [
    'api_bp',
    'document_bp',
    'batch_bp',
    'exception_bp',
    'dashboard_bp'
]