"""
Intelligent Document Processing System
Database connection and operations
"""

import logging
from sqlalchemy.exc import SQLAlchemyError
from app import db

# Configure logging
logger = logging.getLogger(__name__)


def init_db(app):
    """
    Initialize database tables
    
    Args:
        app: Flask application
    """
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created")
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {str(e)}", exc_info=True)
            raise


def drop_all_tables(app, confirm=False):
    """
    Drop all database tables - USE WITH CAUTION
    
    Args:
        app: Flask application
        confirm: Confirmation flag to prevent accidental deletion
    """
    if not confirm:
        logger.warning("Database drop operation cancelled - confirmation required")
        return False
    
    with app.app_context():
        try:
            db.drop_all()
            logger.info("All database tables dropped")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error dropping database tables: {str(e)}", exc_info=True)
            return False


def backup_database(app, filename=None):
    """
    Backup database to file
    
    Args:
        app: Flask application
        filename: Optional filename for backup
        
    Returns:
        str: Path to backup file
    """
    from datetime import datetime
    import os
    import sqlite3
    
    try:
        # Get database URI
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        # Only support SQLite backups for now
        if not db_uri.startswith('sqlite:///'):
            logger.error("Database backup only supports SQLite databases")
            return None
        
        # Extract database path from URI
        db_path = db_uri.replace('sqlite:///', '')
        
        # Generate backup filename if not provided
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backup_{timestamp}.sqlite"
        
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(app.root_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Set backup path
        backup_path = os.path.join(backup_dir, filename)
        
        # Copy database file
        with sqlite3.connect(db_path) as conn:
            backup = sqlite3.connect(backup_path)
            conn.backup(backup)
            backup.close()
        
        logger.info(f"Database backed up to {backup_path}")
        return backup_path
    
    except Exception as e:
        logger.error(f"Error backing up database: {str(e)}", exc_info=True)
        return None


def restore_database(app, backup_path, confirm=False):
    """
    Restore database from backup
    
    Args:
        app: Flask application
        backup_path: Path to backup file
        confirm: Confirmation flag to prevent accidental restore
        
    Returns:
        bool: True if restore was successful, False otherwise
    """
    import os
    import sqlite3
    
    if not confirm:
        logger.warning("Database restore operation cancelled - confirmation required")
        return False
    
    try:
        # Get database URI
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        # Only support SQLite restores for now
        if not db_uri.startswith('sqlite:///'):
            logger.error("Database restore only supports SQLite databases")
            return False
        
        # Extract database path from URI
        db_path = db_uri.replace('sqlite:///', '')
        
        # Check if backup file exists
        if not os.path.exists(backup_path):
            logger.error(f"Backup file {backup_path} not found")
            return False
        
        # Restore database
        with sqlite3.connect(backup_path) as backup:
            conn = sqlite3.connect(db_path)
            backup.backup(conn)
            conn.close()
        
        logger.info(f"Database restored from {backup_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error restoring database: {str(e)}", exc_info=True)
        return False


def get_table_info(app):
    """
    Get information about database tables
    
    Args:
        app: Flask application
        
    Returns:
        dict: Dictionary with table information
    """
    with app.app_context():
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            tables = {}
            for table_name in inspector.get_table_names():
                tables[table_name] = {
                    'columns': inspector.get_columns(table_name),
                    'primary_key': inspector.get_primary_keys(table_name),
                    'foreign_keys': inspector.get_foreign_keys(table_name),
                    'indexes': inspector.get_indexes(table_name)
                }
            
            return tables
        
        except SQLAlchemyError as e:
            logger.error(f"Error getting table information: {str(e)}", exc_info=True)
            return {}


def execute_raw_query(app, query, params=None, fetch=True):
    """
    Execute raw SQL query
    
    Args:
        app: Flask application
        query: SQL query string
        params: Query parameters
        fetch: Whether to fetch results
        
    Returns:
        list: Query results if fetch=True, None otherwise
    """
    with app.app_context():
        try:
            result = db.session.execute(query, params or {})
            
            if fetch:
                return result.fetchall()
            else:
                db.session.commit()
                return None
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error executing query: {str(e)}", exc_info=True)
            raise


def get_model_count(model):
    """
    Get count of records for a model
    
    Args:
        model: SQLAlchemy model class
        
    Returns:
        int: Count of records
    """
    try:
        return model.query.count()
    except SQLAlchemyError as e:
        logger.error(f"Error getting model count: {str(e)}", exc_info=True)
        return 0


def bulk_delete(model, criteria):
    """
    Delete records in bulk
    
    Args:
        model: SQLAlchemy model class
        criteria: Filter criteria
        
    Returns:
        int: Number of records deleted
    """
    try:
        count = model.query.filter_by(**criteria).delete()
        db.session.commit()
        return count
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error in bulk delete: {str(e)}", exc_info=True)
        return 0