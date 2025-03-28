# AI CV Selection System

A simple CV selection application that uses AI to match candidate CVs with job requirements.

## Features

- **Frontend**: Streamlit-based UI for HR professionals
- **Backend**: FastAPI for processing CVs and job requirements
- **AI Integration**: OpenRouter API for CV analysis and matching
- **File Handling**: Support for PDF and DOCX CV formats
- **Containerization**: Docker and Docker Compose for easy deployment

## Project Structure

```
.
├── backend/                # FastAPI backend
│   ├── main.py            # Main API implementation
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # Backend container definition
├── frontend/              # Streamlit frontend
│   ├── app.py             # Streamlit application
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # Frontend container definition
├── docker-compose.yml     # Docker Compose configuration
├── .env                   # Environment variables
└── README.md              # Project documentation
```

## Prerequisites

- Docker and Docker Compose
- OpenRouter API key (https://openrouter.ai/)

## Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd cv-selection-app
```

2. Configure your OpenRouter API key in the `.env` file:

```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

## Running the Application

1. Start the application using Docker Compose:

```bash
docker-compose up -d
```

2. Access the application:

   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000/docs

3. To stop the application:

```bash
docker-compose down
```

## Development

### Running the Backend Locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Running the Frontend Locally

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

## Usage

1. Enter job requirements in the sidebar
2. Upload a candidate's CV (PDF or DOCX format)
3. Click "Analyze CV" to process the CV
4. View the analysis results and matching score
5. Upload multiple CVs to compare candidates

## API Documentation

The backend API documentation is available at http://localhost:8000/docs when the application is running.
