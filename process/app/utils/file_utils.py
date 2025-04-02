"""
Intelligent Document Processing System
File handling utilities
"""

import os
import shutil
import logging
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename

# Try to import magic, but don't fail if not available
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    logging.warning("python-magic library not installed; MIME type detection will be limited")

import ftplib

# Configure logging
logger = logging.getLogger(__name__)

def get_file_extension(filename):
    """
    Get file extension from filename
    
    Args:
        filename: Filename to get extension from
        
    Returns:
        str: File extension (without dot) or empty string if no extension
    """
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ""

def is_allowed_file(filename, allowed_extensions):
    """
    Check if file has allowed extension
    
    Args:
        filename: Filename to check
        allowed_extensions: Set of allowed extensions
        
    Returns:
        bool: True if file is allowed, False otherwise
    """
    extension = get_file_extension(filename)
    return extension in allowed_extensions

def get_safe_filename(filename):
    """
    Get safe filename for storage
    
    Args:
        filename: Original filename
        
    Returns:
        str: Safe filename
    """
    # First secure the filename
    safe_name = secure_filename(filename)
    
    # If filename was completely sanitized, provide a default
    if not safe_name:
        safe_name = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return safe_name

def get_unique_filename(filename, directory):
    """
    Get unique filename for a directory
    
    Args:
        filename: Original filename
        directory: Target directory
        
    Returns:
        str: Unique filename
    """
    if not os.path.exists(os.path.join(directory, filename)):
        return filename
    
    name, extension = os.path.splitext(filename)
    counter = 1
    
    while os.path.exists(os.path.join(directory, f"{name}_{counter}{extension}")):
        counter += 1
    
    return f"{name}_{counter}{extension}"

def save_uploaded_file(file, target_dir, filename=None):
    """
    Save uploaded file to target directory
    
    Args:
        file: File object (from request.files)
        target_dir: Target directory
        filename: Optional custom filename
        
    Returns:
        str: Path to saved file
    """
    try:
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        # Get safe filename
        if filename:
            safe_name = get_safe_filename(filename)
        else:
            safe_name = get_safe_filename(file.filename)
        
        # Ensure filename is unique
        unique_name = get_unique_filename(safe_name, target_dir)
        
        # Save file
        file_path = os.path.join(target_dir, unique_name)
        file.save(file_path)
        
        logger.info(f"File saved to {file_path}")
        return file_path
    
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}", exc_info=True)
        raise

def get_file_hash(file_path):
    """
    Get file hash (MD5)
    
    Args:
        file_path: Path to file
        
    Returns:
        str: File hash
    """
    try:
        md5_hash = hashlib.md5()
        
        with open(file_path, "rb") as f:
            # Read in 4KB chunks
            for byte_block in iter(lambda: f.read(4096), b""):
                md5_hash.update(byte_block)
        
        return md5_hash.hexdigest()
    
    except Exception as e:
        logger.error(f"Error getting file hash: {str(e)}", exc_info=True)
        return None

def get_file_mime_type(file_path):
    """
    Get file MIME type
    
    Args:
        file_path: Path to file
        
    Returns:
        str: MIME type
    """
    try:
        if HAS_MAGIC:
            return magic.from_file(file_path, mime=True)
        else:
            # Fallback to simple extension-based detection
            extension = get_file_extension(file_path)
            mime_types = {
                'pdf': 'application/pdf',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'txt': 'text/plain',
                'csv': 'text/csv',
                'html': 'text/html',
                'xml': 'application/xml',
                'json': 'application/json',
                'zip': 'application/zip',
            }
            return mime_types.get(extension.lower(), 'application/octet-stream')
    except Exception as e:
        logger.error(f"Error getting file MIME type: {str(e)}", exc_info=True)
        return None

def move_file(source_path, target_dir, new_filename=None):
    """
    Move file to target directory
    
    Args:
        source_path: Source file path
        target_dir: Target directory
        new_filename: Optional new filename
        
    Returns:
        str: New file path
    """
    try:
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        # Get filename
        if new_filename:
            target_filename = get_safe_filename(new_filename)
        else:
            target_filename = os.path.basename(source_path)
        
        # Ensure filename is unique
        unique_name = get_unique_filename(target_filename, target_dir)
        
        # Move file
        target_path = os.path.join(target_dir, unique_name)
        shutil.move(source_path, target_path)
        
        logger.info(f"File moved from {source_path} to {target_path}")
        return target_path
    
    except Exception as e:
        logger.error(f"Error moving file: {str(e)}", exc_info=True)
        raise

def copy_file(source_path, target_dir, new_filename=None):
    """
    Copy file to target directory
    
    Args:
        source_path: Source file path
        target_dir: Target directory
        new_filename: Optional new filename
        
    Returns:
        str: New file path
    """
    try:
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        # Get filename
        if new_filename:
            target_filename = get_safe_filename(new_filename)
        else:
            target_filename = os.path.basename(source_path)
        
        # Ensure filename is unique
        unique_name = get_unique_filename(target_filename, target_dir)
        
        # Copy file
        target_path = os.path.join(target_dir, unique_name)
        shutil.copy2(source_path, target_path)
        
        logger.info(f"File copied from {source_path} to {target_path}")
        return target_path
    
    except Exception as e:
        logger.error(f"Error copying file: {str(e)}", exc_info=True)
        raise

def delete_file(file_path):
    """
    Delete file
    
    Args:
        file_path: Path to file
        
    Returns:
        bool: True if deleted, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
            return True
        else:
            logger.warning(f"File not found for deletion: {file_path}")
            return False
    
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}", exc_info=True)
        return False

def create_zip_archive(files, output_path):
    """
    Create ZIP archive from list of files
    
    Args:
        files: List of file paths
        output_path: Output ZIP file path
        
    Returns:
        str: Path to ZIP file
    """
    import zipfile
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create ZIP file
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                if os.path.exists(file_path):
                    # Add file to ZIP with just the filename (not the full path)
                    zipf.write(file_path, os.path.basename(file_path))
        
        logger.info(f"ZIP archive created: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating ZIP archive: {str(e)}", exc_info=True)
        raise

def upload_to_ftp(file_path, ftp_host, ftp_user, ftp_pass, ftp_dir, filename=None):
    """
    Upload file to FTP server
    
    Args:
        file_path: Path to file
        ftp_host: FTP server hostname
        ftp_user: FTP username
        ftp_pass: FTP password
        ftp_dir: FTP directory
        filename: Optional filename on FTP server
        
    Returns:
        bool: True if uploaded, False otherwise
    """
    try:
        # Get filename
        if filename:
            target_filename = filename
        else:
            target_filename = os.path.basename(file_path)
        
        # Connect to FTP server
        with ftplib.FTP(ftp_host) as ftp:
            ftp.login(ftp_user, ftp_pass)
            
            # Change to target directory
            try:
                ftp.cwd(ftp_dir)
            except ftplib.error_perm:
                # Create directory if it doesn't exist
                create_ftp_directory(ftp, ftp_dir)
                ftp.cwd(ftp_dir)
            
            # Upload file
            with open(file_path, 'rb') as f:
                ftp.storbinary(f'STOR {target_filename}', f)
            
            logger.info(f"File uploaded to FTP: {target_filename}")
            return True
    
    except Exception as e:
        logger.error(f"Error uploading to FTP: {str(e)}", exc_info=True)
        return False

def create_ftp_directory(ftp, directory):
    """
    Create directory on FTP server
    
    Args:
        ftp: FTP connection
        directory: Directory path
        
    Returns:
        bool: True if created, False otherwise
    """
    try:
        # Split path into parts
        path_parts = directory.split('/')
        current_path = ""
        
        # Create each part of the path
        for part in path_parts:
            if part:
                current_path += "/" + part
                try:
                    ftp.cwd(current_path)
                except ftplib.error_perm:
                    ftp.mkd(current_path)
        
        return True
    
    except Exception as e:
        logger.error(f"Error creating FTP directory: {str(e)}", exc_info=True)
        return False