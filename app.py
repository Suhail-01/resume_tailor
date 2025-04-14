import streamlit as st
import os
import logging
from dotenv import load_dotenv
from resume_tailorer import generate_tailored_resume
from utils import validate_inputs, set_page_config

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Set page configuration
    set_page_config()
    
    # App title and description
    st.title("AI Resume Tailor")
    st.subheader("Customize your resume for specific job descriptions")
    
    st.markdown("""
    ### How it works:
    1. Paste your current resume
    2. Enter the job description
    3. Click 'Generate Tailored Resume'
    4. Get a customized resume that highlights relevant skills and experience
    """)
    
    # Input sections
    with st.container():
        st.subheader("Your Current Resume")
        resume_text = st.text_area(
            "Paste your current resume here",
            height=300,
            placeholder="Paste your full resume text here...",
            help="Include your skills, experience, education, and other relevant information."
        )
    
    with st.container():
        st.subheader("Job Description")
        job_description = st.text_area(
            "Paste the job description here",
            height=200,
            placeholder="Paste the job description you're applying for...",
            help="Include the full job posting with responsibilities, requirements, and company details."
        )
    
    # Process inputs when button is clicked
    if st.button("Generate Tailored Resume", type="primary"):
        # Validate inputs
        if not validate_inputs(resume_text, job_description):
            st.error("Please provide both your resume and the job description.")
            return
        
        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("OpenAI API key not found. Please set it in your .env file.")
            
            # Show sample response when API key is missing
            st.warning("Since the OpenAI API key is missing, here's a sample response:")
            st.subheader("Sample Tailored Resume")
            
            st.markdown("""
            ### Professional Summary
            *This is a sample response. Please add your OpenAI API key to get personalized results.*
            
            Dedicated software developer with 5+ years of experience in web development. Proficient in JavaScript, Python, and cloud technologies, with a proven track record of delivering scalable solutions. Passionate about creating intuitive user experiences and optimizing application performance.
            
            ### Key Skills Aligned with Job Requirements
            - JavaScript/TypeScript development
            - React.js and modern frontend frameworks
            - Python backend development
            - Cloud infrastructure (AWS)
            - Agile methodologies
            
            ### Tailored Experience Highlights
            - Developed responsive web applications using React.js, improving user engagement by 40%
            - Implemented CI/CD pipelines, reducing deployment time by 60%
            - Collaborated with cross-functional teams to deliver projects on time and within budget
            """)
            return
            
        # Show progress indicator during processing
        with st.spinner("Analyzing your resume and the job description..."):
            try:
                # Generate tailored resume
                tailored_resume = generate_tailored_resume(resume_text, job_description)
                
                # Display results
                st.success("Successfully tailored your resume!")
                st.subheader("Your Tailored Resume")
                st.markdown(tailored_resume)
                
                # Add download button for the tailored resume
                st.download_button(
                    label="Download Tailored Resume",
                    data=tailored_resume,
                    file_name="tailored_resume.md",
                    mime="text/markdown"
                )
                
            except Exception as e:
                logger.error(f"Error generating tailored resume: {str(e)}")
                st.error(f"An error occurred while processing your request: {str(e)}")
                st.info("Please check your inputs and try again.")

if __name__ == "__main__":
    main()
