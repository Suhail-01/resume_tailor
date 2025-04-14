import os
import logging
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_openai_llm():
    """
    Initialize and return the OpenAI language model with configuration.
    
    Returns:
        ChatOpenAI: Configured language model
    """
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    # do not change this unless explicitly requested by the user
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is missing")
        
        return ChatOpenAI(
            model="gpt-4o",
            api_key=api_key,
            temperature=0.7,
            max_tokens=1500
        )
    except Exception as e:
        logger.error(f"Error initializing OpenAI LLM: {str(e)}")
        raise

def create_resume_tailoring_prompt():
    """
    Create the prompt template for resume tailoring.
    
    Returns:
        PromptTemplate: Configured prompt template
    """
    template = """
    You are an expert resume customization assistant. Your task is to tailor a resume to match a specific job description.
    
    RESUME:
    {resume}
    
    JOB DESCRIPTION:
    {job_description}
    
    Please analyze both the resume and job description carefully, then create a tailored version of the resume that:
    1. Creates a compelling professional summary highlighting relevant experience and skills
    2. Identifies and emphasizes skills and experiences that match the job requirements
    3. Rewrites bullet points to use relevant keywords and terminology from the job description
    4. Prioritizes the most relevant achievements and experience for this specific role
    5. Maintains honesty and accuracy - only include skills and experiences actually mentioned in the original resume
    
    Format the tailored resume using markdown with clear sections for:
    - Professional Summary
    - Key Skills Aligned with Job Requirements
    - Tailored Experience Highlights
    - Additional Relevant Information
    
    DO NOT invent new experiences or skills not present in the original resume.
    """
    
    return PromptTemplate(
        input_variables=["resume", "job_description"],
        template=template
    )

def generate_tailored_resume(resume_text, job_description):
    """
    Generate a tailored resume based on the provided resume and job description.
    
    Args:
        resume_text (str): The original resume text
        job_description (str): The job description to tailor the resume for
        
    Returns:
        str: The tailored resume
    """
    try:
        logger.info("Initializing language model")
        llm = get_openai_llm()
        
        logger.info("Creating prompt template")
        prompt_template = create_resume_tailoring_prompt()
        
        logger.info("Setting up LangChain")
        chain = LLMChain(llm=llm, prompt=prompt_template)
        
        logger.info("Generating tailored resume")
        result = chain.run(resume=resume_text, job_description=job_description)
        
        logger.info("Successfully generated tailored resume")
        return result
    
    except Exception as e:
        logger.error(f"Error in generate_tailored_resume: {str(e)}")
        raise Exception(f"Failed to generate tailored resume: {str(e)}")
