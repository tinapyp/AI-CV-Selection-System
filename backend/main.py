import re
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import fitz
import docx
import io
import requests
import os
import json
from typing import List
from pydantic import BaseModel

app = FastAPI(title="CV Selection API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


# Models
class CVAnalysisResult(BaseModel):
    score: int
    analysis: str
    strengths: List[str]
    weaknesses: List[str]


class CandidateResult(BaseModel):
    candidate_name: str
    file_name: str
    score: int
    analysis: str
    strengths: List[str]
    weaknesses: List[str]


# In-memory storage for candidates (in a real app, use a database)
candidates: List[CandidateResult] = []


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = "\n".join([page.get_text() for page in doc])
        return text
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error extracting text from PDF: {str(e)}"
        )


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(io.BytesIO(file_content))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error extracting text from DOCX: {str(e)}"
        )


def extract_text_from_file(file_content: bytes, file_extension: str) -> str:
    """Extract text based on file extension"""
    if file_extension.lower() == ".pdf":
        return extract_text_from_pdf(file_content)
    elif file_extension.lower() == ".docx":
        return extract_text_from_docx(file_content)
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload PDF or DOCX files.",
        )


def analyze_cv_with_llm(cv_text: str, job_desc: str) -> CVAnalysisResult:
    """Analyze CV using OpenRouter API"""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured")

    prompt = f"""
    You are an AI assistant helping HR professionals evaluate job candidates.
    
    JOB REQUIREMENTS:
    {job_desc}
    
    CANDIDATE CV:
    {cv_text}
    
    Please analyze how well this candidate matches the job requirements. 
    Provide your response in the following JSON format:
    {{
        "score": [a number between 0-100 representing match percentage],
        "analysis": [a detailed analysis of the candidate's fit for the position],
        "strengths": [a list of the candidate's key strengths relevant to the position],
        "weaknesses": [a list of areas where the candidate may not meet requirements]
    }}
    
    Return ONLY the JSON object with no additional text.
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek/deepseek-r1-distill-llama-70b",
        "messages": [{"role": "user", "content": prompt}],
        # "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(OPENROUTER_ENDPOINT, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()

        # Extract the content from the response
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        match = re.search(r"```json(.*?)```", content, re.DOTALL)
        # Parse the JSON content
        analysis_result = json.loads(match.group(1).strip())

        return CVAnalysisResult(
            score=analysis_result.get("score", 0),
            analysis=analysis_result.get("analysis", "No analysis provided"),
            strengths=analysis_result.get("strengths", []),
            weaknesses=analysis_result.get("weaknesses", []),
        )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Error calling OpenRouter API: {str(e)}"
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500, detail=f"Error parsing OpenRouter API response: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def extract_candidate_name(cv_text: str) -> str:
    """Extract candidate name from CV text (simplified version)"""
    # In a real application, use more sophisticated NLP techniques
    lines = cv_text.split("\n")
    # Simple heuristic: take the first non-empty line as the name
    for line in lines:
        if line.strip():
            return line.strip()
    return "Unknown Candidate"


@app.post("/api/analyze-cv/", response_model=CVAnalysisResult)
async def analyze_cv(file: UploadFile = File(...), job_description: str = Form(...)):
    """Analyze a CV against job requirements"""
    # Get file extension
    file_extension = os.path.splitext(file.filename)[1]

    # Read file content
    file_content = await file.read()

    # Extract text from file
    cv_text = extract_text_from_file(file_content, file_extension)

    # Analyze CV
    result = analyze_cv_with_llm(cv_text, job_description)

    # Extract candidate name
    candidate_name = extract_candidate_name(cv_text)

    # Store candidate result
    candidate_result = CandidateResult(
        candidate_name=candidate_name,
        file_name=file.filename,
        score=result.score,
        analysis=result.analysis,
        strengths=result.strengths,
        weaknesses=result.weaknesses,
    )

    candidates.append(candidate_result)

    return result


@app.get("/api/candidates/", response_model=List[CandidateResult])
async def get_candidates():
    """Get all analyzed candidates sorted by score (highest first)"""
    sorted_candidates = sorted(candidates, key=lambda x: x.score, reverse=True)
    return sorted_candidates


@app.delete("/api/candidates/")
async def clear_candidates():
    """Clear all candidates (for testing purposes)"""
    candidates.clear()
    return {"message": "All candidates cleared"}


@app.get("/api/health/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
