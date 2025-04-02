"""
Intelligent Document Processing System
Utilities module initialization
"""

# Import file utilities
from app.utils.file_utils import (
    get_file_extension,
    is_allowed_file,
    get_safe_filename,
    get_unique_filename,
    save_uploaded_file,
    get_file_hash,
    get_file_mime_type,
    move_file,
    copy_file,
    delete_file,
    create_zip_archive,
    upload_to_ftp,
    create_ftp_directory
)

# Import helper utilities
from app.utils.helpers import (
    CustomJSONEncoder,
    to_json,
    from_json,
    to_xml,
    from_xml,
    format_currency,
    format_phone,
    format_date,
    truncate_text,
    get_file_size_str,
    get_document_type_display,
    generate_batch_name,
    mask_sensitive_data,
    get_progress_percentage
)

# Export utility functions
__all__ = [
    # File utilities
    'get_file_extension',
    'is_allowed_file',
    'get_safe_filename',
    'get_unique_filename',
    'save_uploaded_file',
    'get_file_hash',
    'get_file_mime_type',
    'move_file',
    'copy_file',
    'delete_file',
    'create_zip_archive',
    'upload_to_ftp',
    'create_ftp_directory',
    
    # Helper utilities
    'CustomJSONEncoder',
    'to_json',
    'from_json',
    'to_xml',
    'from_xml',
    'format_currency',
    'format_phone',
    'format_date',
    'truncate_text',
    'get_file_size_str',
    'get_document_type_display',
    'generate_batch_name',
    'mask_sensitive_data',
    'get_progress_percentage'
]