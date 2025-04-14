import os
import json
import logging
from typing import Dict, List, Tuple, Any
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain_community.chat_models import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MatchScore(BaseModel):
    """Class for match score results between resume and job description."""
    percentage: int = Field(description="Overall match percentage between resume and job requirements (0-100)")
    matched_skills: List[str] = Field(description="List of skills from the resume that match the job requirements")
    missing_skills: List[str] = Field(description="List of skills in the job requirements that are missing from the resume")
    keyword_matches: Dict[str, int] = Field(description="Dictionary of job keywords found in resume with their occurrence count")

class ResumeAnalysis(BaseModel):
    """Class for detailed resume analysis."""
    strengths: List[str] = Field(description="List of resume strengths relevant to the job")
    improvement_areas: List[str] = Field(description="List of suggested improvements to better match the job")
    keyword_recommendations: List[str] = Field(description="Keywords to incorporate from the job description")
    ats_optimization_tips: List[str] = Field(description="Tips for optimizing the resume for ATS systems")

def get_openai_llm(temperature=0.7, max_tokens=1500):
    """
    Initialize and return the OpenAI language model with configuration.
    
    Args:
        temperature (float): Controls randomness in output (0.0 to 1.0)
        max_tokens (int): Maximum number of tokens to generate
    
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
            temperature=temperature,
            max_tokens=max_tokens
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
    system_template = """
    You are an expert resume customization assistant with deep knowledge of ATS (Applicant Tracking Systems) and modern hiring practices.
    Your task is to tailor a resume to match a specific job description and make it stand out to both automated systems and human recruiters.
    """
    
    human_template = """
    # RESUME
    ```
    {resume}
    ```
    
    # JOB DESCRIPTION
    ```
    {job_description}
    ```
    
    First, carefully analyze both the resume and job description to identify alignment and gaps. Then create a tailored version that:

    1. Creates a compelling professional summary that positions the candidate as ideal for this specific role
    2. Identifies and emphasizes skills, experiences, and achievements that directly match the job requirements
    3. Rewrites bullet points to strategically incorporate relevant keywords and terminology from the job description
    4. Reorders and prioritizes content to highlight the most relevant experience for this role
    5. Maintains complete honesty - only include skills and experiences actually mentioned in the original resume
    6. Optimizes formatting and language for ATS systems while remaining appealing to human readers
    
    ## OUTPUT FORMAT
    Format the tailored resume using markdown with clear sections for:
    - Professional Summary
    - Key Skills Aligned with Job Requirements (in a clean bullet point format)
    - Tailored Experience Highlights (focus on accomplishments with metrics where possible)
    - Education & Certifications (if relevant to the job)
    - Additional Relevant Information
    
    Use professional, confident language that demonstrates expertise without exaggeration.
    """
    
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    
    chat_prompt = ChatPromptTemplate.from_messages([
        system_message_prompt,
        human_message_prompt
    ])
    
    return chat_prompt

def create_match_analysis_prompt():
    """
    Create a prompt for analyzing the match between resume and job description.
    
    Returns:
        ChatPromptTemplate: Configured prompt template
    """
    system_template = """
    You are an AI expert in job matching and resume analysis with deep understanding of ATS systems.
    Your task is to analyze the match between a resume and job description and provide concrete data and actionable insights.
    """
    
    human_template = """
    # RESUME
    ```
    {resume}
    ```
    
    # JOB DESCRIPTION
    ```
    {job_description}
    ```
    
    Analyze how well this resume matches the job requirements. Provide your response in the following JSON format:
    
    ```json
    {{
        "percentage": <overall match percentage between 0-100>,
        "matched_skills": [<list of skills in the resume that match job requirements>],
        "missing_skills": [<list of important skills from job description not found in resume>],
        "keyword_matches": {{
            "<keyword1>": <occurrence count>,
            "<keyword2>": <occurrence count>
        }}
    }}
    ```
    
    Look for both exact keyword matches and conceptual matches (skills described differently but meaning the same thing).
    Provide only the JSON with no additional text.
    """
    
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    
    chat_prompt = ChatPromptTemplate.from_messages([
        system_message_prompt,
        human_message_prompt
    ])
    
    return chat_prompt

def create_resume_analysis_prompt():
    """
    Create a prompt for detailed resume analysis and improvement recommendations.
    
    Returns:
        ChatPromptTemplate: Configured prompt template
    """
    system_template = """
    You are an elite resume consultant who specializes in helping candidates stand out. 
    Your task is to analyze a resume in relation to a job description and provide specific, actionable recommendations.
    """
    
    human_template = """
    # RESUME
    ```
    {resume}
    ```
    
    # JOB DESCRIPTION
    ```
    {job_description}
    ```
    
    Analyze this resume in relation to the job description and provide detailed recommendations. 
    Format your response as the following JSON:
    
    ```json
    {{
        "strengths": [<list of 3-5 resume strengths relevant to this job>],
        "improvement_areas": [<list of 3-5 specific improvements to better match the job>],
        "keyword_recommendations": [<list of 5-10 important keywords from the job to incorporate>],
        "ats_optimization_tips": [<list of 3-5 specific tips to make this resume more ATS-friendly>]
    }}
    ```
    
    Provide only the JSON with no additional text.
    """
    
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    
    chat_prompt = ChatPromptTemplate.from_messages([
        system_message_prompt,
        human_message_prompt
    ])
    
    return chat_prompt

def generate_match_score(resume_text: str, job_description: str) -> MatchScore:
    """
    Generate a match score analysis between resume and job description.
    
    Args:
        resume_text (str): The original resume text
        job_description (str): The job description
        
    Returns:
        MatchScore: Object containing match analysis
    """
    try:
        logger.info("Analyzing resume-job match score")
        llm = get_openai_llm(temperature=0.2, max_tokens=1000)
        
        match_prompt = create_match_analysis_prompt()
        match_chain = LLMChain(llm=llm, prompt=match_prompt)
        
        match_result = match_chain.run(resume=resume_text, job_description=job_description)
        
        # Parse JSON response into MatchScore object
        match_data = json.loads(match_result)
        match_score = MatchScore(
            percentage=match_data.get("percentage", 0),
            matched_skills=match_data.get("matched_skills", []),
            missing_skills=match_data.get("missing_skills", []),
            keyword_matches=match_data.get("keyword_matches", {})
        )
        
        logger.info(f"Generated match score: {match_score.percentage}%")
        return match_score
        
    except Exception as e:
        logger.error(f"Error generating match score: {str(e)}")
        raise Exception(f"Failed to generate match analysis: {str(e)}")

def generate_resume_analysis(resume_text: str, job_description: str) -> ResumeAnalysis:
    """
    Generate detailed analysis and recommendations for resume improvement.
    
    Args:
        resume_text (str): The original resume text
        job_description (str): The job description
        
    Returns:
        ResumeAnalysis: Object containing analysis and recommendations
    """
    try:
        logger.info("Generating detailed resume analysis")
        llm = get_openai_llm(temperature=0.3, max_tokens=1000)
        
        analysis_prompt = create_resume_analysis_prompt()
        analysis_chain = LLMChain(llm=llm, prompt=analysis_prompt)
        
        analysis_result = analysis_chain.run(resume=resume_text, job_description=job_description)
        
        # Parse JSON response into ResumeAnalysis object
        analysis_data = json.loads(analysis_result)
        resume_analysis = ResumeAnalysis(
            strengths=analysis_data.get("strengths", []),
            improvement_areas=analysis_data.get("improvement_areas", []),
            keyword_recommendations=analysis_data.get("keyword_recommendations", []),
            ats_optimization_tips=analysis_data.get("ats_optimization_tips", [])
        )
        
        logger.info("Successfully generated resume analysis")
        return resume_analysis
        
    except Exception as e:
        logger.error(f"Error generating resume analysis: {str(e)}")
        raise Exception(f"Failed to generate resume analysis: {str(e)}")

def generate_tailored_resume(resume_text: str, job_description: str) -> str:
    """
    Generate a tailored resume based on the provided resume and job description.
    
    Args:
        resume_text (str): The original resume text
        job_description (str): The job description to tailor the resume for
        
    Returns:
        str: The tailored resume formatted in markdown
    """
    try:
        logger.info("Initializing language model for resume tailoring")
        llm = get_openai_llm(temperature=0.5, max_tokens=1800)
        
        logger.info("Creating tailored resume prompt")
        prompt_template = create_resume_tailoring_prompt()
        
        logger.info("Setting up LangChain for resume generation")
        chain = LLMChain(llm=llm, prompt=prompt_template)
        
        logger.info("Generating tailored resume")
        result = chain.run(resume=resume_text, job_description=job_description)
        
        logger.info("Successfully generated tailored resume")
        return result
    
    except Exception as e:
        logger.error(f"Error in generate_tailored_resume: {str(e)}")
        raise Exception(f"Failed to generate tailored resume: {str(e)}")

def get_full_resume_analysis(resume_text: str, job_description: str) -> Tuple[str, MatchScore, ResumeAnalysis]:
    """
    Perform complete resume analysis and tailoring.
    
    Args:
        resume_text (str): The original resume text
        job_description (str): The job description
        
    Returns:
        Tuple[str, MatchScore, ResumeAnalysis]: Tailored resume, match score, and analysis
    """
    try:
        # Generate all components in parallel (in a real-world scenario, these could be parallelized)
        tailored_resume = generate_tailored_resume(resume_text, job_description)
        match_score = generate_match_score(resume_text, job_description)
        resume_analysis = generate_resume_analysis(resume_text, job_description)
        
        return tailored_resume, match_score, resume_analysis
        
    except Exception as e:
        logger.error(f"Error in get_full_resume_analysis: {str(e)}")
        raise Exception(f"Failed to complete resume analysis: {str(e)}")
