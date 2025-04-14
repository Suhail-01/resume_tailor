import streamlit as st
import logging
import io
import os
from pypdf import PdfReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_page_config():
    """
    Configure the Streamlit page settings.
    """
    st.set_page_config(
        page_title="AI Resume Tailor Pro",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def extract_text_from_pdf(pdf_file):
    """
    Extract text from a PDF file.
    
    Args:
        pdf_file: The uploaded PDF file object
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        
        if not text.strip():
            logger.warning("No text extracted from PDF")
            return None
            
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

def validate_uploaded_file(uploaded_file):
    """
    Validate the uploaded resume file.
    
    Args:
        uploaded_file: The uploaded file object
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if uploaded_file is None:
        return False, None
    
    # Check file size (2MB limit)
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > 2:
        return False, f"File size exceeds 2MB limit (current size: {file_size_mb:.2f}MB)"
    
    # Check file type
    file_type = uploaded_file.type
    if "pdf" not in file_type.lower():
        return False, f"Only PDF files are supported (received: {file_type})"
    
    return True, None

def validate_inputs(resume_text, job_description):
    """
    Validate the user inputs to ensure they are not empty.
    
    Args:
        resume_text (str): The resume text input
        job_description (str): The job description input
        
    Returns:
        bool: True if inputs are valid, False otherwise
    """
    if not resume_text or not resume_text.strip():
        logger.warning("Empty resume text submitted")
        return False
    
    if not job_description or not job_description.strip():
        logger.warning("Empty job description submitted")
        return False
    
    return True

def sanitize_input(text):
    """
    Sanitize input text to prevent potential security issues.
    
    Args:
        text (str): The input text to sanitize
        
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Basic sanitization - remove potentially dangerous HTML/script tags
    # For a production app, consider using a proper HTML sanitizer library
    sanitized = text.replace("<script>", "").replace("</script>", "")
    return sanitized
