"""
Intelligent Document Processing System
Main application initialization
"""

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask extensions
db = SQLAlchemy()

def create_app(config=None):
    """
    Application factory function to create and configure the Flask app
    """
    app = Flask(__name__, 
                static_folder='../static',
                template_folder='../templates')
    
    # Load configuration
    if config:
        app.config.from_object(config)
    else:
        app.config.from_object('app.config.DevelopmentConfig')
    
    # Initialize extensions with app
    CORS(app)
    db.init_app(app)
    
    # Register blueprints
    from app.api.routes import api_bp
    from app.api.document_routes import document_bp
    from app.api.batch_routes import batch_bp
    from app.api.exception_routes import exception_bp
    from app.api.dashboard_routes import dashboard_bp
    
    app.register_blueprint(api_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(batch_bp)
    app.register_blueprint(exception_bp)
    app.register_blueprint(dashboard_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app