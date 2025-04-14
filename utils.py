import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_page_config():
    """
    Configure the Streamlit page settings.
    """
    st.set_page_config(
        page_title="AI Resume Tailor",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

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
