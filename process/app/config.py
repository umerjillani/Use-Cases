"""
Intelligent Document Processing System
Configuration settings
"""

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration class"""
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'taurus-idp-secret-key'
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(basedir), 'data', 'raw')
    PROCESSED_FOLDER = os.path.join(os.path.dirname(basedir), 'data', 'processed')
    FAILED_FOLDER = os.path.join(os.path.dirname(basedir), 'data', 'failed')
    BATCHES_FOLDER = os.path.join(os.path.dirname(basedir), 'data', 'batches')
    EXPORTED_FOLDER = os.path.join(os.path.dirname(basedir), 'data', 'exported')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    ALLOWED_EXTENSIONS = {'pdf', 'tiff', 'tif'}
    
    # OCR and AI settings
    OCR_ENGINE = 'tesseract'  # Options: 'tesseract', 'azure', 'google'
    AI_MODEL_PATH = os.path.join(os.path.dirname(basedir), 'models')
    
    # FTP Settings
    FTP_HOST = os.environ.get('FTP_HOST') or 'ftp.example.com'
    FTP_USER = os.environ.get('FTP_USER') or 'user'
    FTP_PASS = os.environ.get('FTP_PASS') or 'password'
    FTP_DIR = os.environ.get('FTP_DIR') or '/upload'
    
    # Logging
    LOG_FOLDER = os.path.join(os.path.dirname(basedir), 'logs')
    
    # Create necessary directories if they don't exist
    @staticmethod
    def init_app(app):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
        os.makedirs(app.config['FAILED_FOLDER'], exist_ok=True)
        os.makedirs(app.config['BATCHES_FOLDER'], exist_ok=True)
        os.makedirs(app.config['EXPORTED_FOLDER'], exist_ok=True)
        os.makedirs(app.config['LOG_FOLDER'], exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(basedir), 'data-dev.sqlite')
    # More verbose logging
    LOGGING_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(basedir), 'data-test.sqlite')
    # Use test data directories
    UPLOAD_FOLDER = os.path.join(os.path.dirname(basedir), 'tests', 'data', 'raw')
    PROCESSED_FOLDER = os.path.join(os.path.dirname(basedir), 'tests', 'data', 'processed')
    FAILED_FOLDER = os.path.join(os.path.dirname(basedir), 'tests', 'data', 'failed')
    BATCHES_FOLDER = os.path.join(os.path.dirname(basedir), 'tests', 'data', 'batches')
    EXPORTED_FOLDER = os.path.join(os.path.dirname(basedir), 'tests', 'data', 'exported')
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    # Use in-memory processing for tests
    OCR_ENGINE = 'mock'


class ProductionConfig(Config):
    """Production configuration"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(basedir), 'data.sqlite')
    # Less verbose logging
    LOGGING_LEVEL = 'INFO'
    
    # Stronger security settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}