# Resume Tailor

Resume Tailor is an advanced AI-powered application that helps job seekers customize their resumes for specific job applications to increase their chances of getting past Applicant Tracking Systems (ATS) and impressing recruiters.

## Features

- **Resume Tailoring**: Automatically tailors your resume to match job descriptions
- **ATS Optimization**: Makes your resume ATS-friendly with proper formatting and keywords
- **Match Score Analysis**: Shows how well your resume matches the job requirements
- **Keyword Optimization**: Identifies important keywords from the job description
- **Skills Gap Analysis**: Highlights matched skills and missing skills
- **Multiple Model Support**: Works with OpenAI GPT-4o, Anthropic Claude, or a free model option
- **PDF Upload**: Easily upload PDF resumes with automatic text extraction
- **Multiple Export Options**: Download results as Markdown or plain text

## How It Works

1. **Upload or paste your resume** and the job description
2. **Get an ATS-optimized resume** tailored specifically for the job
3. **See your match score** and detailed analysis
4. **Apply with confidence** knowing your resume is optimized

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Required Python packages (listed in requirements.txt)
- Optional: OpenAI or Anthropic API key for best results

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/Suhail-01/resume-tailor.git
   cd resume-tailor
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. (Optional) Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

4. Run the application:
   ```
   streamlit run app.py
   ```

5. Open your browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

## API Key Configuration

You can use Resume Tailor in several ways:
- With OpenAI API (best results)
- With Anthropic Claude API (also excellent)
- With a free model option (limited functionality)

API keys can be provided in three ways:
1. In a `.env` file (for local development)
2. Through the UI in the sidebar's "API Key Settings" section
3. As environment variables if deploying to a server

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Streamlit, LangChain, and advanced AI models
- Special thanks to OpenAI and Anthropic for their powerful APIs