import os
import json
import logging
import sys
import requests
import anthropic
from typing import Dict, List, Tuple, Any, Optional, Union, Literal
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.chains import LLMChain, SequentialChain
# Remove duplicate import - using the community version is the correct approach
# from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain_community.chat_models import ChatOpenAI
from langchain.schema.language_model import BaseLanguageModel

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

def direct_anthropic_call(system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 1500) -> str:
    """
    Make a direct API call to Anthropic Claude.
    
    Args:
        system_prompt (str): The system instructions for Claude
        user_prompt (str): The user prompt to send to Claude
        temperature (float): Controls randomness in output (0.0 to 1.0)
        max_tokens (int): Maximum number of tokens to generate
        
    Returns:
        str: The generated response text
    """
    try:
        # Check for Anthropic API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        # If no API key, use a different approach - in this case we'll simulate a free approach
        if not api_key:
            logger.info("No Anthropic API key found, using free model approach")
            # We'll use a direct call to a free API endpoint - here's a simulated free model approach
            return call_free_model(system_prompt, user_prompt)
        
        # If we have an API key, use the official Anthropic client
        client = anthropic.Anthropic(api_key=api_key)
        # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logger.info("Successfully generated response from Anthropic Claude")
        return message.content[0].text
        
    except Exception as e:
        logger.error(f"Error in direct Anthropic call: {str(e)}")
        # Fallback to free model
        logger.info("Falling back to free model")
        return call_free_model(system_prompt, user_prompt)

def call_free_model(system_prompt: str, user_prompt: str) -> str:
    """
    Make a call to a free model as a fallback option.
    
    Args:
        system_prompt (str): The system prompt for context
        user_prompt (str): The user prompt to send
        
    Returns:
        str: The generated response text
    """
    try:
        # Make a call to the OpenAI free tier model like gpt-3.5-turbo with gpt-4o-mini
        url = "https://api.openai.com/v1/chat/completions"
        
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": combined_prompt}
            ]
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            logger.error(f"Error with free model: {response.status_code} - {response.text}")
            return f"I apologize, but I couldn't generate a response due to API limitations. Please try again later or provide API credentials for better results."
            
    except Exception as e:
        logger.error(f"Error in free model call: {str(e)}")
        return "I apologize, but I couldn't generate a response due to API limitations. Please try again later or provide API credentials for better results."

def get_model(model_choice: str = "auto", temperature: float = 0.7, max_tokens: int = 1500) -> Optional[BaseLanguageModel]:
    """
    Initialize and return the appropriate language model based on availability.
    
    Args:
        model_choice (str): The model to use ('openai', 'anthropic', 'free', or 'auto')
        temperature (float): Controls randomness in output (0.0 to 1.0)
        max_tokens (int): Maximum number of tokens to generate
    
    Returns:
        Optional[BaseLanguageModel]: Configured language model or None if using direct API
    """
    # Check if model_choice is being overridden by environment
    env_model = os.getenv("RESUME_TAILORER_MODEL")
    if env_model:
        logger.info(f"Using model from environment: {env_model}")
        model_choice = env_model
    
    # Check OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Check Anthropic API key
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Log available API keys (without showing the actual keys)
    logger.info(f"OpenAI API key available: {bool(openai_api_key)}")
    logger.info(f"Anthropic API key available: {bool(anthropic_api_key)}")
    
    # If model_choice is auto, try to determine the best one
    if model_choice == "auto":
        if openai_api_key:
            model_choice = "openai"
        elif anthropic_api_key:
            model_choice = "anthropic"
        else:
            model_choice = "free"
        logger.info(f"Auto-selected model: {model_choice}")
    
    # Initialize appropriate model
    if model_choice == "openai" and openai_api_key:
        try:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            logger.info("Using OpenAI GPT-4o model")
            return ChatOpenAI(
                model="gpt-4o",
                api_key=openai_api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            logger.error(f"Error initializing OpenAI LLM: {str(e)}")
            # If OpenAI fails, try Anthropic if available
            if anthropic_api_key:
                model_choice = "anthropic"
                logger.info("Falling back to Anthropic model")
            else:
                model_choice = "free"
                logger.info("Falling back to free model")
    
    # For now, we'll use direct API calls for Anthropic and free models
    logger.info(f"Using direct API call with model: {model_choice}")
    # Return None to signal using direct API calls
    return None

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
        
        # Try to get a language model
        try:
            llm = get_model(temperature=0.2, max_tokens=1000)  # Will use environment model choice
        except:
            llm = None
        
        # Get the prompts
        match_prompt = create_match_analysis_prompt()
        
        # If we have a language model (OpenAI), use LangChain
        if llm:
            logger.info("Using LangChain with OpenAI for match score analysis")
            match_chain = LLMChain(llm=llm, prompt=match_prompt)
            match_result = match_chain.run(resume=resume_text, job_description=job_description)
        else:
            # Otherwise use direct API call
            logger.info("Using direct API call for match score analysis")
            system_prompt = match_prompt.messages[0].prompt.template
            user_prompt = match_prompt.messages[1].prompt.template.format(
                resume=resume_text, 
                job_description=job_description
            )
            match_result = direct_anthropic_call(system_prompt, user_prompt, temperature=0.2, max_tokens=1000)
        
        # Parse JSON response into MatchScore object
        try:
            match_data = json.loads(match_result)
        except json.JSONDecodeError:
            # If result is not valid JSON, try to extract JSON from the text
            import re
            json_pattern = re.search(r'```json\s*(.*?)\s*```', match_result, re.DOTALL)
            if json_pattern:
                try:
                    match_data = json.loads(json_pattern.group(1))
                except:
                    # Create default values as fallback
                    match_data = {
                        "percentage": 50,
                        "matched_skills": ["Generic skill match"],
                        "missing_skills": ["Could not analyze missing skills"],
                        "keyword_matches": {"keywords": 1}
                    }
            else:
                # Create default values as fallback
                match_data = {
                    "percentage": 50,
                    "matched_skills": ["Generic skill match"],
                    "missing_skills": ["Could not analyze missing skills"],
                    "keyword_matches": {"keywords": 1}
                }
        
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
        # Return a default match score as fallback
        return MatchScore(
            percentage=50,
            matched_skills=["Unable to analyze skills accurately"],
            missing_skills=["Unable to analyze missing skills"],
            keyword_matches={"error": 1}
        )

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
        
        # Try to get a language model
        try:
            llm = get_model(temperature=0.3, max_tokens=1000)  # Will use environment model choice
        except:
            llm = None
        
        # Get the prompts
        analysis_prompt = create_resume_analysis_prompt()
        
        # If we have a language model (OpenAI), use LangChain
        if llm:
            logger.info("Using LangChain with OpenAI for resume analysis")
            analysis_chain = LLMChain(llm=llm, prompt=analysis_prompt)
            analysis_result = analysis_chain.run(resume=resume_text, job_description=job_description)
        else:
            # Otherwise use direct API call
            logger.info("Using direct API call for resume analysis")
            system_prompt = analysis_prompt.messages[0].prompt.template
            user_prompt = analysis_prompt.messages[1].prompt.template.format(
                resume=resume_text, 
                job_description=job_description
            )
            analysis_result = direct_anthropic_call(system_prompt, user_prompt, temperature=0.3, max_tokens=1000)
        
        # Parse JSON response into ResumeAnalysis object
        try:
            analysis_data = json.loads(analysis_result)
        except json.JSONDecodeError:
            # If result is not valid JSON, try to extract JSON from the text
            import re
            json_pattern = re.search(r'```json\s*(.*?)\s*```', analysis_result, re.DOTALL)
            if json_pattern:
                try:
                    analysis_data = json.loads(json_pattern.group(1))
                except:
                    # Create default values as fallback
                    analysis_data = {
                        "strengths": ["Your resume contains relevant experience"],
                        "improvement_areas": ["Consider highlighting your skills more clearly"],
                        "keyword_recommendations": ["job-specific keywords"],
                        "ats_optimization_tips": ["Use standard section headings"]
                    }
            else:
                # Create default values as fallback
                analysis_data = {
                    "strengths": ["Your resume contains relevant experience"],
                    "improvement_areas": ["Consider highlighting your skills more clearly"],
                    "keyword_recommendations": ["job-specific keywords"],
                    "ats_optimization_tips": ["Use standard section headings"]
                }
        
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
        # Return a default analysis as fallback
        return ResumeAnalysis(
            strengths=["Your resume contains relevant experience"],
            improvement_areas=["Consider highlighting your skills more clearly"],
            keyword_recommendations=["job-specific keywords"],
            ats_optimization_tips=["Use standard section headings"]
        )

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
        
        # Try to get a language model
        try:
            llm = get_model(temperature=0.5, max_tokens=1800)  # Will use environment model choice
        except:
            llm = None
        
        # Get the prompts
        prompt_template = create_resume_tailoring_prompt()
        
        # If we have a language model (OpenAI), use LangChain
        if llm:
            logger.info("Using LangChain with OpenAI for resume tailoring")
            chain = LLMChain(llm=llm, prompt=prompt_template)
            result = chain.run(resume=resume_text, job_description=job_description)
        else:
            # Otherwise use direct API call
            logger.info("Using direct API call for resume tailoring")
            system_prompt = prompt_template.messages[0].prompt.template
            user_prompt = prompt_template.messages[1].prompt.template.format(
                resume=resume_text, 
                job_description=job_description
            )
            result = direct_anthropic_call(system_prompt, user_prompt, temperature=0.5, max_tokens=1800)
        
        logger.info("Successfully generated tailored resume")
        return result
    
    except Exception as e:
        logger.error(f"Error in generate_tailored_resume: {str(e)}")
        # Return a simpler version as fallback
        return f"""
# Tailored Resume

## Professional Summary
I'm sorry, but I couldn't generate a fully tailored resume due to API limitations. 
Here's a simple version based on your original resume:

{resume_text[:500] + "..." if len(resume_text) > 500 else resume_text}

## Next Steps
Please try again later or provide API credentials for better results.
"""

def generate_tailored_resume_with_model(resume_text: str, job_description: str, model_choice: str = "auto") -> str:
    """
    Generate a tailored resume using the specified model.
    
    Args:
        resume_text (str): The original resume text
        job_description (str): The job description
        model_choice (str): Which model to use ("auto", "openai", "anthropic", or "free")
        
    Returns:
        str: The tailored resume
    """
    try:
        logger.info(f"Generating tailored resume using model: {model_choice}")
        
        # Set environment variable for model choice
        os.environ["RESUME_TAILORER_MODEL"] = model_choice
        
        # Call the regular function (it will use the model choice from environment)
        return generate_tailored_resume(resume_text, job_description)
        
    except Exception as e:
        logger.error(f"Error in generate_tailored_resume_with_model: {str(e)}")
        return f"""
# Tailored Resume

## Professional Summary
I'm sorry, but I couldn't generate a fully tailored resume due to API limitations. 
Here's a simple version based on your original resume:

{resume_text[:500] + "..." if len(resume_text) > 500 else resume_text}

## Next Steps
Please try again later or provide API credentials for better results.
"""

def generate_match_score_with_model(resume_text: str, job_description: str, model_choice: str = "auto") -> MatchScore:
    """
    Generate a match score using the specified model.
    
    Args:
        resume_text (str): The original resume text
        job_description (str): The job description
        model_choice (str): Which model to use ("auto", "openai", "anthropic", or "free")
        
    Returns:
        MatchScore: The match score analysis
    """
    try:
        logger.info(f"Generating match score using model: {model_choice}")
        
        # Set environment variable for model choice
        os.environ["RESUME_TAILORER_MODEL"] = model_choice
        
        # Call the regular function (it will use the model choice from environment)
        return generate_match_score(resume_text, job_description)
        
    except Exception as e:
        logger.error(f"Error in generate_match_score_with_model: {str(e)}")
        # Return a default match score as fallback
        return MatchScore(
            percentage=50,
            matched_skills=["Unable to analyze skills accurately"],
            missing_skills=["Unable to analyze missing skills"],
            keyword_matches={"error": 1}
        )

def generate_resume_analysis_with_model(resume_text: str, job_description: str, model_choice: str = "auto") -> ResumeAnalysis:
    """
    Generate a resume analysis using the specified model.
    
    Args:
        resume_text (str): The original resume text
        job_description (str): The job description
        model_choice (str): Which model to use ("auto", "openai", "anthropic", or "free")
        
    Returns:
        ResumeAnalysis: The resume analysis
    """
    try:
        logger.info(f"Generating resume analysis using model: {model_choice}")
        
        # Set environment variable for model choice
        os.environ["RESUME_TAILORER_MODEL"] = model_choice
        
        # Call the regular function (it will use the model choice from environment)
        return generate_resume_analysis(resume_text, job_description)
        
    except Exception as e:
        logger.error(f"Error in generate_resume_analysis_with_model: {str(e)}")
        # Return a default analysis as fallback
        return ResumeAnalysis(
            strengths=["Your resume contains relevant experience"],
            improvement_areas=["Consider highlighting your skills more clearly"],
            keyword_recommendations=["job-specific keywords"],
            ats_optimization_tips=["Use standard section headings"]
        )

def get_full_resume_analysis(resume_text: str, job_description: str) -> Tuple[str, MatchScore, ResumeAnalysis]:
    """
    Perform complete resume analysis and tailoring.
    
    Args:
        resume_text (str): The original resume text
        job_description (str): The job description
        
    Returns:
        Tuple[str, MatchScore, ResumeAnalysis]: Tailored resume, match score, and analysis
    """
    return get_full_resume_analysis_with_model(resume_text, job_description, "auto")

def get_full_resume_analysis_with_model(resume_text: str, job_description: str, model_choice: str = "auto") -> Tuple[str, MatchScore, ResumeAnalysis]:
    """
    Perform complete resume analysis and tailoring with the specified model.
    
    Args:
        resume_text (str): The original resume text
        job_description (str): The job description
        model_choice (str): Which model to use ("auto", "openai", "anthropic", or "free")
        
    Returns:
        Tuple[str, MatchScore, ResumeAnalysis]: Tailored resume, match score, and analysis
    """
    try:
        logger.info(f"Performing full resume analysis using model: {model_choice}")
        
        # Generate all components with the specified model
        tailored_resume = generate_tailored_resume_with_model(resume_text, job_description, model_choice)
        match_score = generate_match_score_with_model(resume_text, job_description, model_choice)
        resume_analysis = generate_resume_analysis_with_model(resume_text, job_description, model_choice)
        
        return tailored_resume, match_score, resume_analysis
        
    except Exception as e:
        logger.error(f"Error in get_full_resume_analysis_with_model: {str(e)}")
        # Create fallback responses
        tailored_resume = f"""
# Tailored Resume

## Professional Summary
I'm sorry, but I couldn't generate a fully tailored resume due to API limitations. 
Here's a simple version based on your original resume:

{resume_text[:500] + "..." if len(resume_text) > 500 else resume_text}

## Next Steps
Please try again later or provide API credentials for better results.
"""
        match_score = MatchScore(
            percentage=50,
            matched_skills=["Unable to analyze skills accurately"],
            missing_skills=["Unable to analyze missing skills"],
            keyword_matches={"error": 1}
        )
        resume_analysis = ResumeAnalysis(
            strengths=["Your resume contains relevant experience"],
            improvement_areas=["Consider highlighting your skills more clearly"],
            keyword_recommendations=["job-specific keywords"],
            ats_optimization_tips=["Use standard section headings"]
        )
        
        return tailored_resume, match_score, resume_analysis
