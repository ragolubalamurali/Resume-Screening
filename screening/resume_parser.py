import os
import re
import json
import docx
import PyPDF2
import io
import logging
from django.conf import settings

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

logger = logging.getLogger(__name__)

# Configure genai if key is available
def get_api_key():
    return getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY'))

def extract_text_from_file(uploaded_file):
    filename = uploaded_file.name.lower()
    text = ""
    
    try:
        if filename.endswith('.txt'):
            text = uploaded_file.read().decode('utf-8', errors='ignore')
        elif filename.endswith('.pdf'):
            # PyPDF2 requires file stream
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        elif filename.endswith('.docx'):
            # python-docx requires file stream
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        raise ValueError(f"Could not read {filename}: {str(e)}")
        
    return text

def parse_resume_text(text):
    """
    Parses resume text to extract education, experience, projects_count and skills.
    Uses Gemini LLM if GEMINI_API_KEY is configured, otherwise falls back to regex heuristics.
    """
    api_key = get_api_key()
    if HAS_GENAI and api_key:
        try:
            return _parse_with_gemini(text, api_key)
        except Exception as e:
            logger.error(f"Gemini parsing failed, falling back to regex: {e}")
            return _parse_with_regex(text)
    else:
        return _parse_with_regex(text)

def _parse_with_gemini(text, api_key):
    client = genai.Client(api_key=api_key)
    prompt = f"""
    You are an expert resume parser. Extract the following information from the resume text below and return ONLY a valid JSON object.
    Do not wrap the JSON in markdown code blocks. Just return the raw JSON string.

    Required fields:
    - skills (string): A comma-separated list of all technical and soft skills mentioned.
    - experience (float): Total years of professional work experience as a number (e.g. 2.5). Estimate based on dates if not explicitly stated. If it's a fresher resume with no work experience, use 0.0.
    - education (string): Choose ONE of the following exactly based on the highest degree: 'B.Sc', 'B.Tech', 'M.Tech', 'MBA', 'PhD'. If something else, map it to the closest equivalent (e.g. BE -> B.Tech).
    - projects_count (integer): The total number of projects the candidate has worked on.

    Resume text:
    {text[:8000]}
    """
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    response_text = response.text.strip()
    
    # clean markdown if present
    if response_text.startswith("```json"):
        response_text = response_text[7:-3].strip()
    elif response_text.startswith("```"):
        response_text = response_text[3:-3].strip()
    
    data = json.loads(response_text)
    
    # Validation
    valid_edu = ["B.Sc", "B.Tech", "M.Tech", "MBA", "PhD"]
    education = data.get('education', 'B.Tech')
    if education not in valid_edu:
        education = "B.Tech"
        
    return {
        'skills': str(data.get('skills', '')),
        'experience': float(data.get('experience', 0.0)),
        'education': education,
        'projects_count': int(data.get('projects_count', 1))
    }

def _parse_with_regex(text):
    text_lower = text.lower()
    
    # 1. Extract Education
    education = "B.Tech" # Default
    if re.search(r'\b(phd|ph\.d|doctorate)\b', text_lower):
        education = "PhD"
    elif re.search(r'\b(m\.tech|mtech|master of technology)\b', text_lower):
        education = "M.Tech"
    elif re.search(r'\b(mba|master of business administration)\b', text_lower):
        education = "MBA"
    elif re.search(r'\b(b\.tech|btech|bachelor of technology)\b', text_lower):
        education = "B.Tech"
    elif re.search(r'\b(b\.sc|bsc|bachelor of science)\b', text_lower):
        education = "B.Sc"

    # 2. Extract Experience (Years)
    experience = 0.0
    exp_matches = re.findall(r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s*of)?\s*experience', text_lower)
    if exp_matches:
        experience = max([float(m) for m in exp_matches])
    
    # 3. Extract Projects Count
    word_projects_count = len(re.findall(r'\bprojects?\b', text_lower))
    projects_section_count = 0
    projects_match = re.search(r'\bprojects\b(.*?)(?:\b(skills|education|experience|certifications)\b|$)', text_lower, re.DOTALL)
    if projects_match:
        section_text = projects_match.group(1)
        bullets = re.findall(r'(?:[•\-*]|\d+\.)', section_text)
        if len(bullets) > 0:
            projects_section_count = max(1, len(bullets) // 2)
            
    projects_count = max(word_projects_count, projects_section_count)
    if projects_count == 0:
        projects_count = 1

    # 4. Skills
    skills = " ".join(text.split())
    skills = skills[:5000]
    
    return {
        'skills': skills,
        'experience': experience,
        'education': education,
        'projects_count': projects_count
    }
