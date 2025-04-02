"""
Intelligent Document Processing System
Main application entry point
"""

import os
import logging
from flask import render_template, redirect, url_for, request
from app import create_app
from app.config import config

# Create application instance with the appropriate configuration
app_env = os.environ.get('FLASK_ENV', 'default')
app = create_app(config[app_env])

# Configure logging
logging.basicConfig(
    level=getattr(logging, app.config.get('LOGGING_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(app.config['LOG_FOLDER'], 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize app with configuration-specific setup
with app.app_context():
    config[app_env].init_app(app)
    logger.info(f"Application started in {app_env} mode")


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/upload')
@app.route('/document-upload')  # Add alias route
def upload():
    """Document upload page"""
    return render_template('document_upload.html')


@app.route('/batches')
def batches():
    """Batch management page"""
    return render_template('batch_management.html')


@app.route('/exceptions')
def exceptions():
    """Exceptions management page"""
    return render_template('exceptions.html')


@app.route('/documents')
def documents():
    """Processed documents page"""
    return render_template('processed_documents.html')


@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 error page"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    """Custom 500 error page"""
    logger.error(f"Server error: {e}")
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)