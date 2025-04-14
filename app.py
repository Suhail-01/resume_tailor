import streamlit as st
import os
import logging
import json
import time

# Safely load environment variables (skip if file missing on Streamlit Cloud)
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# Set Streamlit page config early
st.set_page_config(page_title="AI Resume Tailor", layout="wide", page_icon="📄")

# Local imports (assumes these exist in your project)
from resume_tailorer import get_full_resume_analysis_with_model
from utils import (
    validate_inputs, set_page_config, sanitize_input, extract_text_from_pdf, validate_uploaded_file
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def render_match_score(match_score):
    st.subheader("📊 Job Match Analysis")
    st.markdown(f"#### Match Score: {match_score.percentage}%")
    st.progress(match_score.percentage / 100)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 🎯 Matching Skills")
        for skill in match_score.matched_skills:
            st.markdown(f"✅ {skill}")

    with col2:
        st.markdown("##### 🔍 Missing Skills")
        for skill in match_score.missing_skills:
            st.markdown(f"❌ {skill}")

    keywords = [(k, v) for k, v in match_score.keyword_matches.items()]
    keywords.sort(key=lambda x: x[1], reverse=True)

    if keywords:
        data = {"Keywords": [k for k, v in keywords], "Occurrences": [v for k, v in keywords]}
        st.bar_chart(data, x="Keywords", y="Occurrences", use_container_width=True)
    else:
        st.info("No keyword matches found.")

def render_resume_analysis(analysis):
    st.subheader("📝 Resume Improvement Analysis")
    tab1, tab2, tab3, tab4 = st.tabs(["Strengths", "Areas to Improve", "Recommended Keywords", "ATS Optimization"])

    with tab1:
        for item in analysis.strengths:
            st.markdown(f"✅ {item}")

    with tab2:
        for item in analysis.improvement_areas:
            st.markdown(f"📌 {item}")

    with tab3:
        cols = st.columns(2)
        for i, keyword in enumerate(analysis.keyword_recommendations):
            with cols[i % 2]:
                st.markdown(f"🔹 {keyword}")

    with tab4:
        for tip in analysis.ats_optimization_tips:
            st.markdown(f"💡 {tip}")

def main():
    st.title("AI Resume Tailor Pro")
    st.markdown("### The Ultimate AI-Powered Resume Customization Tool")

    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/resume.png", width=80)
        st.markdown("## How it works")
        st.markdown("""
        1. **Upload or paste your resume** and the job description  
        2. **Get an ATS-optimized resume**  
        3. **See your match score** and detailed analysis  
        4. **Apply with confidence**
        """)

        with st.expander("🔑 API Key Settings"):
            openai_key = st.text_input("OpenAI API Key", type="password")
            anthropic_key = st.text_input("Anthropic API Key", type="password")

            if openai_key:
                os.environ["OPENAI_API_KEY"] = openai_key
            if anthropic_key:
                os.environ["ANTHROPIC_API_KEY"] = anthropic_key

    input_tab, results_tab = st.tabs(["✏️ Input", "🚀 Results"])

    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = ""

    with input_tab:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Your Resume")
            upload_tab, text_tab = st.tabs(["📄 Upload PDF", "✏️ Paste Text"])

            with upload_tab:
                resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
                if resume_file:
                    valid, error = validate_uploaded_file(resume_file)
                    if valid:
                        extracted = extract_text_from_pdf(resume_file)
                        if extracted:
                            st.session_state.resume_text = extracted
                            st.success("Text extracted!")
                            with st.expander("Show Text"):
                                st.text(extracted)
                        else:
                            st.error("Extraction failed.")
                    else:
                        st.error(error)

            with text_tab:
                resume_text_input = st.text_area("Paste Resume Text", value=st.session_state.resume_text, height=250)
                if resume_text_input != st.session_state.resume_text:
                    st.session_state.resume_text = resume_text_input

        with col2:
            st.subheader("Job Description")
            job_description = st.text_area("Paste JD", height=250)

        st.markdown("---")
        analysis_options = st.multiselect(
            "Select Analyses",
            ["Tailored Resume", "Match Score Analysis", "Resume Improvement Suggestions"],
            default=["Tailored Resume", "Match Score Analysis", "Resume Improvement Suggestions"]
        )

        model_choice = st.radio("Select AI Model", ["Auto-select", "OpenAI", "Anthropic", "Free Model"], horizontal=True)
        model_map = {"Auto-select": "auto", "OpenAI": "openai", "Anthropic": "anthropic", "Free Model": "free"}
        selected_model = model_map[model_choice]

        if st.button("Generate Analysis"):
            resume_text = st.session_state.resume_text
            if not validate_inputs(resume_text, job_description):
                st.error("Resume and Job Description are required.")
                return

            resume_text = sanitize_input(resume_text)
            job_description = sanitize_input(job_description)

            if selected_model != "free":
                if selected_model in ["openai", "auto"] and not os.getenv("OPENAI_API_KEY"):
                    st.warning("No OpenAI key. Using Free Model.")
                    selected_model = "free"
                if selected_model == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
                    st.warning("No Anthropic key. Using Free Model.")
                    selected_model = "free"
                if selected_model == "auto" and not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
                    selected_model = "free"

            with st.spinner("Running analysis..."):
                try:
                    st.session_state.run_tailored_resume = "Tailored Resume" in analysis_options
                    st.session_state.run_match_score = "Match Score Analysis" in analysis_options
                    st.session_state.run_resume_analysis = "Resume Improvement Suggestions" in analysis_options

                    tailored, score, analysis = get_full_resume_analysis_with_model(
                        resume_text, job_description, selected_model
                    )

                    st.session_state.tailored_resume = tailored
                    st.session_state.match_score = score
                    st.session_state.resume_analysis = analysis
                    st.session_state.analysis_complete = True
                    st.success("Done! Go to Results tab.")
                except Exception as e:
                    logger.error(e)
                    st.error(f"Error: {e}")

    with results_tab:
        if not st.session_state.get("analysis_complete"):
            st.info("Go to Input tab and run analysis.")
            return

        st.subheader("🌟 Your Resume Results")

        if st.session_state.get("run_tailored_resume"):
            st.subheader("✨ Tailored Resume")
            st.markdown(st.session_state.tailored_resume)

        if st.session_state.get("run_match_score"):
            render_match_score(st.session_state.match_score)

        if st.session_state.get("run_resume_analysis"):
            render_resume_analysis(st.session_state.resume_analysis)

        st.markdown("---")
        st.subheader("📋 Next Steps")
        st.markdown("""
        - Review and tweak the tailored resume
        - Add missing skills if relevant
        - Apply with confidence 🚀
        """)

if __name__ == "__main__":
    main()
