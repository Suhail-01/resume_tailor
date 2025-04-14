import streamlit as st

# This is a minimal starter file guaranteed to run on Streamlit Cloud
# Once this deploys successfully, you can rename it back to app.py and add your features

st.set_page_config(
    page_title="Resume Tailor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("AI Resume Tailor")
st.markdown("### The Ultimate AI-Powered Resume Customization Tool")
st.write("This is a minimal version to test deployment. Full app coming soon!")

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/resume.png", width=80)
    st.markdown("## Resume Tailor Pro")
    st.markdown("Optimize your resume for ATS systems")

st.info("App is successfully running on Streamlit Cloud! 🎉")