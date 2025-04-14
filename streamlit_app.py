import streamlit as st

# This is the most minimal Streamlit app possible
# This file is guaranteed to pass health checks on Streamlit Cloud
# Once it's working, you can gradually add features

# Set page config at the very top
st.set_page_config(
    page_title="Resume Tailor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title
st.title("AI Resume Tailor Pro")
st.markdown("### The Ultimate AI-Powered Resume Customization Tool")

# Display info for users
st.info("The app is loading... please wait a moment.")

# Add minimal sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/resume.png", width=80)
    st.markdown("## Resume Tailor")
    st.markdown("Optimize your resume for ATS systems")

# Add a simple placeholder for the main content
st.write("App is successfully running! 🎉")
st.markdown("""
## How it works:
1. Upload or paste your resume
2. Paste the job description 
3. Get an ATS-optimized resume
""")

# Add a debugging section
with st.expander("Debug Info"):
    st.write("App Version: 1.0.0")
    st.write("Status: Running")