import streamlit as st

# Set page config at the very top (required for Streamlit Cloud)
try:
    st.set_page_config(
        page_title="Resume Tailor",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception as e:
    # This might happen if set_page_config was already called
    st.error(f"Error setting page config: {str(e)}")

import os
import logging
import json
import time
import traceback

# Safely load environment variables (skip if file missing on Streamlit Cloud)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception as e:
    st.warning(f"Note: .env file not loaded, using environment variables directly: {str(e)}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Protect imports with try-except to help diagnose Streamlit Cloud issues
try:
    from resume_tailorer import get_full_resume_analysis_with_model, MatchScore, ResumeAnalysis
    from utils import validate_inputs, sanitize_input, extract_text_from_pdf, validate_uploaded_file
except Exception as e:
    st.error(f"Error importing modules: {str(e)}")
    st.code(traceback.format_exc())

def render_match_score(match_score):
    """Render match score analysis in the UI"""
    st.subheader("📊 Job Match Analysis")
    
    # Match percentage gauge visualization
    st.markdown(f"#### Match Score: {match_score.percentage}%")
    st.progress(match_score.percentage/100)
    
    # Skills analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🎯 Matching Skills")
        for skill in match_score.matched_skills:
            st.markdown(f"✅ {skill}")
    
    with col2:
        st.markdown("##### 🔍 Missing Skills")
        for skill in match_score.missing_skills:
            st.markdown(f"❌ {skill}")
    
    # Keyword Analysis
    st.markdown("##### 🔑 Keyword Matches")
    
    # Convert to list of tuples and sort by count (descending)
    keywords = [(k, v) for k, v in match_score.keyword_matches.items()]
    keywords.sort(key=lambda x: x[1], reverse=True)
    
    # Display as a horizontal bar chart
    if keywords:
        keywords_data = {
            "Keywords": [k for k, v in keywords],
            "Occurrences": [v for k, v in keywords]
        }
        st.bar_chart(keywords_data, x="Keywords", y="Occurrences", use_container_width=True)
    else:
        st.info("No keyword matches found.")

def render_resume_analysis(resume_analysis):
    """Render detailed resume analysis in the UI"""
    st.subheader("📝 Resume Improvement Analysis")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Strengths", "Areas to Improve", "Recommended Keywords", "ATS Optimization"])
    
    with tab1:
        st.markdown("#### 💪 Your Resume Strengths")
        for strength in resume_analysis.strengths:
            st.markdown(f"✅ {strength}")
    
    with tab2:
        st.markdown("#### 🔨 Areas to Improve")
        for area in resume_analysis.improvement_areas:
            st.markdown(f"📌 {area}")
    
    with tab3:
        st.markdown("#### 🔑 Recommended Keywords")
        cols = st.columns(2)
        for i, keyword in enumerate(resume_analysis.keyword_recommendations):
            col_idx = i % 2
            with cols[col_idx]:
                st.markdown(f"🔹 {keyword}")
    
    with tab4:
        st.markdown("#### 🤖 ATS Optimization Tips")
        for tip in resume_analysis.ats_optimization_tips:
            st.markdown(f"💡 {tip}")

def main():
    # App title and description
    st.title("AI Resume Tailor Pro")
    st.markdown("### The Ultimate AI-Powered Resume Customization Tool")
    
    # Sidebar with info
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/resume.png", width=80)
        st.markdown("## How it works")
        st.markdown("""
        1. **Upload or paste your resume** and the job description
        2. **Get an ATS-optimized resume** tailored specifically for the job
        3. **See your match score** and detailed analysis
        4. **Apply with confidence** knowing your resume is optimized
        
        Developed with advanced AI technologies:
        - OpenAI GPT-4o
        - LangChain
        - ATS Optimization
        """)
        
        st.markdown("---")
        
        # API Key Configuration
        with st.expander("🔑 API Key Settings"):
            st.caption("Add your API keys for better results")
            
            # OpenAI Key Input
            openai_key = st.text_input(
                "OpenAI API Key", 
                type="password",
                placeholder="sk-...",
                help="Enter your OpenAI API key for GPT-4o access"
            )
            
            # Anthropic Key Input
            anthropic_key = st.text_input(
                "Anthropic API Key", 
                type="password",
                placeholder="sk-ant-...",
                help="Enter your Anthropic API key for Claude access"
            )
            
            # Set the API keys as environment variables if provided
            if openai_key:
                os.environ["OPENAI_API_KEY"] = openai_key
                
            if anthropic_key:
                os.environ["ANTHROPIC_API_KEY"] = anthropic_key
            
            st.caption("Your API keys are not stored and will be cleared when you refresh the page")
        
        st.markdown("---")
        st.markdown("### 💼 Why this matters")
        st.markdown("""
        - **75%** of resumes are rejected by ATS before a human sees them
        - Tailored resumes are **8x more likely** to get interviews
        - Most recruiters spend **< 7 seconds** reviewing a resume
        """)
    
    # Create tabs for different sections
    input_tab, results_tab = st.tabs(["✏️ Input Your Information", "🚀 View Results"])
    
    # Initialize session state for resume_text
    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = ""
    
    with input_tab:
        # Input sections
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Your Current Resume")
            
            # Create tabs for PDF upload and text input
            resume_tabs = st.tabs(["📄 Upload PDF", "✏️ Paste Text"])
            
            with resume_tabs[0]:
                # PDF upload option
                resume_file = st.file_uploader(
                    "Upload your resume (PDF only, max 2MB)",
                    type=["pdf"],
                    help="We'll extract the text from your PDF resume automatically."
                )
                
                if resume_file is not None:
                    try:
                        # Validate the uploaded file
                        is_valid, error_message = validate_uploaded_file(resume_file)
                        
                        if not is_valid:
                            st.error(error_message)
                        else:
                            # Extract text from PDF
                            extracted_text = extract_text_from_pdf(resume_file)
                            
                            if extracted_text:
                                st.success("Resume uploaded and text extracted successfully!")
                                st.session_state.resume_text = extracted_text
                                st.markdown("### Preview:")
                                with st.expander("Show extracted text"):
                                    st.text(extracted_text)
                            else:
                                st.error("Could not extract text from the PDF. Please try pasting your resume text directly.")
                    except Exception as e:
                        st.error(f"Error processing PDF: {str(e)}")
                        st.info("Please try pasting your resume text directly.")
            
            with resume_tabs[1]:
                # Text input option
                resume_text_input = st.text_area(
                    "Paste your current resume here",
                    value=st.session_state.resume_text,
                    height=300,
                    placeholder="Paste your full resume text here...",
                    help="Include your skills, experience, education, and other relevant information."
                )
                
                # Update session state if text area changed
                if resume_text_input != st.session_state.resume_text:
                    st.session_state.resume_text = resume_text_input
        
        with col2:
            st.subheader("Job Description")
            job_description = st.text_area(
                "Paste the job description here",
                height=300,
                placeholder="Paste the job description you're applying for...",
                help="Include the full job posting with responsibilities, requirements, and company details."
            )
        
        # Options and generate button
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            analysis_options = st.multiselect(
                "Analysis Options",
                options=["Tailored Resume", "Match Score Analysis", "Resume Improvement Suggestions"],
                default=["Tailored Resume", "Match Score Analysis", "Resume Improvement Suggestions"],
                help="Select which analyses you want to receive"
            )
            
            # Model selection
            model_choice = st.radio(
                "Select AI Model (using free model if no API key available)",
                options=["Auto-select", "OpenAI (requires API key)", "Anthropic Claude (requires API key)", "Free Model"],
                index=0,
                horizontal=True,
                help="Select which AI model to use for analysis. 'Auto-select' will use the best available model."
            )
            
            # Map radio options to model identifiers
            model_mapping = {
                "Auto-select": "auto",
                "OpenAI (requires API key)": "openai",
                "Anthropic Claude (requires API key)": "anthropic",
                "Free Model": "free"
            }
            
            selected_model = model_mapping[model_choice]
        
        with col2:
            generate_button = st.button("Generate Analysis", type="primary")
            
        if generate_button:
            # Get resume_text from session state
            resume_text = st.session_state.resume_text
            
            # Validate inputs
            try:
                if not validate_inputs(resume_text, job_description):
                    st.error("Please provide both your resume and the job description.")
                    st.stop()
                
                # Sanitize inputs
                resume_text = sanitize_input(resume_text)
                job_description = sanitize_input(job_description)
            except Exception as e:
                st.error(f"Error validating inputs: {str(e)}")
                st.stop()
            
            # Check for API keys if not using free model
            try:
                if selected_model != "free":
                    # For both auto and openai options, check OpenAI key
                    if selected_model == "openai" or selected_model == "auto":
                        openai_api_key = os.getenv("OPENAI_API_KEY")
                        if not openai_api_key and selected_model == "openai":
                            st.warning("OpenAI API key not found. Switching to free model.")
                            selected_model = "free"
                    
                    # For anthropic, check Anthropic key
                    if selected_model == "anthropic":
                        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
                        if not anthropic_api_key:
                            st.warning("Anthropic API key not found. Switching to free model.")
                            selected_model = "free"
                    
                    # If auto was selected but no API keys are available, use free model
                    if selected_model == "auto":
                        openai_api_key = os.getenv("OPENAI_API_KEY")
                        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
                        if not openai_api_key and not anthropic_api_key:
                            st.info("No API keys found. Using the free model option.")
                            selected_model = "free"
            except Exception as e:
                st.warning(f"Error checking API keys: {str(e)}. Continuing with free model.")
                selected_model = "free"
            
            # Process and analyze
            with st.spinner("Analyzing your resume and the job description... (this may take a minute)"):
                try:
                    # Save to session state for the results tab
                    if "Tailored Resume" in analysis_options:
                        st.session_state.run_tailored_resume = True
                    
                    if "Match Score Analysis" in analysis_options:
                        st.session_state.run_match_score = True
                    
                    if "Resume Improvement Suggestions" in analysis_options:
                        st.session_state.run_resume_analysis = True
                    
                    # Display model info to user
                    if selected_model == "free":
                        st.info("Using free model for analysis. For better results, provide an API key.")
                    elif selected_model == "openai":
                        st.info("Using OpenAI GPT model for analysis.")
                    elif selected_model == "anthropic":
                        st.info("Using Anthropic Claude model for analysis.")
                    else:  # auto
                        st.info("Using best available model for analysis.")
                    
                    # Add model info to session state
                    st.session_state.model_used = selected_model
                    
                    # Run the full analysis with the selected model
                    tailored_resume, match_score, resume_analysis = get_full_resume_analysis_with_model(
                        resume_text, job_description, selected_model
                    )
                    
                    # Store results in session state
                    st.session_state.tailored_resume = tailored_resume
                    st.session_state.match_score = match_score
                    st.session_state.resume_analysis = resume_analysis
                    st.session_state.analysis_complete = True
                    
                    # Switch to results tab
                    st.success("Analysis complete! Check the Results tab.")
                    
                except Exception as e:
                    logger.error(f"Error during analysis: {str(e)}")
                    st.error(f"An error occurred while processing your request: {str(e)}")
                    st.info("Please check your inputs and try again with a free model or provide API keys.")
    
    with results_tab:
        if 'analysis_complete' not in st.session_state or not st.session_state.analysis_complete:
            st.info("Please input your resume and job description in the Input tab, then click 'Generate Analysis'.")
            return
            
        # Display all results
        st.subheader("🌟 Your Resume Analysis Results")
        
        # Tailored Resume section
        if 'run_tailored_resume' in st.session_state and st.session_state.run_tailored_resume:
            st.markdown("---")
            st.subheader("✨ Your Tailored Resume")
            st.markdown(st.session_state.tailored_resume)
            
            # Download options
            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button(
                    label="Download as Markdown (.md)",
                    data=st.session_state.tailored_resume,
                    file_name="tailored_resume.md",
                    mime="text/markdown"
                )
            with col2:
                # Add plain text version
                plain_text = st.session_state.tailored_resume.replace('###', '').replace('##', '').replace('#', '')
                st.download_button(
                    label="Download as Text (.txt)",
                    data=plain_text,
                    file_name="tailored_resume.txt",
                    mime="text/plain"
                )
            with col3:
                # Add option to copy to clipboard
                st.button("Copy to Clipboard", 
                          help="Click to copy the tailored resume to your clipboard")
        
        # Match Score Analysis
        if 'run_match_score' in st.session_state and st.session_state.run_match_score:
            st.markdown("---")
            render_match_score(st.session_state.match_score)
        
        # Resume Improvement Analysis
        if 'run_resume_analysis' in st.session_state and st.session_state.run_resume_analysis:
            st.markdown("---")
            render_resume_analysis(st.session_state.resume_analysis)
        
        # Tips for next steps
        st.markdown("---")
        st.subheader("📋 Next Steps")
        st.markdown("""
        1. **Review your tailored resume** and make any necessary manual adjustments
        2. **Incorporate the suggested keywords** to further optimize for ATS
        3. **Consider addressing the missing skills** in your resume or cover letter
        4. **Apply with confidence** knowing your resume is optimized for this position
        """)

# Debug section for Streamlit Cloud deployment 
if 'debug' in st.query_params:
    with st.expander("Debug information", expanded=True):
        st.write("Debugging mode active")
        st.write(f"Streamlit version: {st.__version__}")
        st.write(f"Current working directory: {os.getcwd()}")
        st.write(f"Files in current directory: {os.listdir('.')}")
        
        try:
            st.write("Dependencies successfully imported")
        except Exception as e:
            st.error(f"Import error: {str(e)}")
            st.code(traceback.format_exc())

# Call the main function inside a try/except to catch any startup errors
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.code(traceback.format_exc())
        st.info("Please report this error to the development team.")
else:
    # This ensures something is displayed when imported (for Streamlit Cloud health checks)
    try:
        main()
    except Exception as e:
        st.title("Resume Tailor App")
        st.error(f"Error during module import: {str(e)}")
        st.info("Try refreshing the page or contact support if the issue persists.")