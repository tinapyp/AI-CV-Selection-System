import streamlit as st
import requests
import json
import os
from typing import List, Dict, Any

# API Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")

# Page configuration
st.set_page_config(
    page_title="AI CV Selection System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #0D47A1;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid #1E88E5;
    }
    .score-high {
        font-size: 1.5rem;
        color: #2E7D32;
        font-weight: bold;
    }
    .score-medium {
        font-size: 1.5rem;
        color: #F9A825;
        font-weight: bold;
    }
    .score-low {
        font-size: 1.5rem;
        color: #C62828;
        font-weight: bold;
    }
    .strength {
        background-color: #E8F5E9;
        padding: 5px 10px;
        border-radius: 5px;
        margin: 5px;
        display: inline-block;
    }
    .weakness {
        background-color: #FFEBEE;
        padding: 5px 10px;
        border-radius: 5px;
        margin: 5px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

def get_score_class(score: int) -> str:
    """Return CSS class based on score"""
    if score >= 70:
        return "score-high"
    elif score >= 50:
        return "score-medium"
    else:
        return "score-low"

def display_candidate_card(candidate: Dict[str, Any]):
    """Display a candidate card with all information"""
    with st.container():
        st.markdown(f'<div class="card">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {candidate['candidate_name']}")
            st.markdown(f"**File:** {candidate['file_name']}")
        
        with col2:
            st.markdown(
                f"<div class='{get_score_class(candidate['score'])}'>Score: {candidate['score']}/100</div>", 
                unsafe_allow_html=True
            )
        
        st.markdown("#### Analysis")
        st.write(candidate["analysis"])
        
        st.markdown("#### Strengths")
        strengths_html = " ".join([f'<span class="strength">{strength}</span>' for strength in candidate["strengths"]])
        st.markdown(strengths_html, unsafe_allow_html=True)
        
        st.markdown("#### Weaknesses")
        weaknesses_html = " ".join([f'<span class="weakness">{weakness}</span>' for weakness in candidate["weaknesses"]])
        st.markdown(weaknesses_html, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Sidebar
    st.sidebar.markdown('<div class="main-header">AI CV Selection</div>', unsafe_allow_html=True)
    
    # Job Requirements Section
    st.sidebar.markdown('<div class="section-header">Job Requirements</div>', unsafe_allow_html=True)
    job_description = st.sidebar.text_area(
        "Enter the job requirements and qualifications",
        height=300,
        help="Describe the position, required skills, experience, education, etc."
    )
    
    # CV Upload Section
    st.sidebar.markdown('<div class="section-header">Upload CV</div>', unsafe_allow_html=True)
    uploaded_file = st.sidebar.file_uploader(
        "Upload candidate CV",
        type=["pdf", "docx"],
        help="Supported formats: PDF, DOCX"
    )
    
    # Process Button
    process_cv = st.sidebar.button("Analyze CV", type="primary", disabled=not (uploaded_file and job_description))
    
    # Clear All Button
    if st.sidebar.button("Clear All Candidates"):
        try:
            response = requests.delete(f"{BACKEND_URL}/api/candidates/")
            if response.status_code == 200:
                st.sidebar.success("All candidates cleared successfully")
            else:
                st.sidebar.error(f"Error clearing candidates: {response.text}")
        except requests.RequestException as e:
            st.sidebar.error(f"Error connecting to backend: {str(e)}")
    
    # Main content area
    st.markdown('<div class="main-header">AI CV Selection System</div>', unsafe_allow_html=True)
    
    # Process the CV if button is clicked
    if process_cv and uploaded_file and job_description:
        with st.spinner("Analyzing CV... This may take a moment."):
            try:
                # Prepare the file and data
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"job_description": job_description}
                
                # Send to backend
                response = requests.post(
                    f"{BACKEND_URL}/api/analyze-cv/",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"CV analyzed successfully! Score: {result['score']}/100")
                else:
                    st.error(f"Error analyzing CV: {response.text}")
            except requests.RequestException as e:
                st.error(f"Error connecting to backend: {str(e)}")
    
    # Display all candidates
    try:
        response = requests.get(f"{BACKEND_URL}/api/candidates/")
        if response.status_code == 200:
            candidates = response.json()
            
            if candidates:
                st.markdown('<div class="section-header">Candidates Ranking</div>', unsafe_allow_html=True)
                
                for candidate in candidates:
                    display_candidate_card(candidate)
            else:
                st.info("No candidates analyzed yet. Upload a CV and job description to get started.")
        else:
            st.error(f"Error fetching candidates: {response.text}")
    except requests.RequestException as e:
        st.error(f"Error connecting to backend: {str(e)}")

if __name__ == "__main__":
    main()
