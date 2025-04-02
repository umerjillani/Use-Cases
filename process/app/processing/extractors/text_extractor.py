"""
Intelligent Document Processing System
Text extraction utility
"""

import os
import logging
import pytesseract
from PIL import Image
import cv2
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

def extract_text_from_image(image_path):
    """
    Extract text from an image using OCR
    
    Args:
        image_path: Path to the image file
        
    Returns:
        str: Extracted text
    """
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Failed to read image at {image_path}")
            return ""
        
        # Preprocess the image to improve OCR accuracy
        preprocessed_img = preprocess_image(img)
        
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(preprocessed_img)
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}", exc_info=True)
        return ""

def preprocess_image(img):
    """
    Preprocess the image to improve OCR accuracy
    
    Args:
        img: Image as numpy array
        
    Returns:
        PIL.Image: Preprocessed image
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get black and white image
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        # Noise removal
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Convert back to PIL Image for pytesseract
        pil_img = Image.fromarray(opening)
        
        return pil_img
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}", exc_info=True)
        # Return original image as PIL Image if preprocessing fails
        return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

def extract_text_from_region(img, x, y, w, h):
    """
    Extract text from a specific region of an image
    
    Args:
        img: Image as numpy array
        x, y: Top-left corner coordinates
        w, h: Width and height of the region
        
    Returns:
        str: Extracted text
    """
    try:
        # Extract region
        region = img[y:y+h, x:x+w]
        
        # Preprocess the region
        preprocessed_region = preprocess_image(region)
        
        # Extract text
        text = pytesseract.image_to_string(preprocessed_region)
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from region: {str(e)}", exc_info=True)
        return ""

def extract_structured_data(img, regions):
    """
    Extract structured data from an image using predefined regions
    
    Args:
        img: Image as numpy array
        regions: Dictionary of regions with keys as field names and values as (x, y, w, h) tuples
        
    Returns:
        dict: Dictionary with field names as keys and extracted text as values
    """
    result = {}
    
    try:
        for field_name, (x, y, w, h) in regions.items():
            text = extract_text_from_region(img, x, y, w, h)
            result[field_name] = text.strip()
    except Exception as e:
        logger.error(f"Error extracting structured data: {str(e)}", exc_info=True)
    
    return result