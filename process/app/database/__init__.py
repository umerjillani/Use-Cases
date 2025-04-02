"""
Intelligent Document Processing System
Database module initialization
"""

from app.database.db import (
    init_db,
    drop_all_tables,
    backup_database,
    restore_database,
    get_table_info,
    execute_raw_query,
    get_model_count,
    bulk_delete
)

# Export all database functions
__all__ = [
    'init_db',
    'drop_all_tables',
    'backup_database',
    'restore_database',
    'get_table_info',
    'execute_raw_query',
    'get_model_count',
    'bulk_delete'
]