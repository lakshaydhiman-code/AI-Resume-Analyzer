# ⚡ ResumeLab / AI Resume Analyzer

A production-grade, full-stack AI Resume Analyzer and ATS Optimization web platform built with FastAPI, SQLAlchemy (PostgreSQL / SQLite fallback), PyMuPDF, Tesseract OCR, Google Gemini AI, and Vanilla JS.

---

## 🌟 Key Features

1. **Authentication System**:
   - Secure JWT token-based authentication with bcrypt password hashing.
   - User registration (`POST /auth/signup`), login (`POST /auth/login`), profile (`GET /auth/me`).
   - Strict multi-tenant isolation: Users only ever access their own resumes.

2. **Multi-Stage PDF Processing & OCR Pipeline**:
   - **Normal PDF Text Extraction**: PyMuPDF (`fitz`) parses text from digital PDFs.
   - **OCR for Scanned PDFs**: High-resolution page rendering (250 DPI) + grayscale/contrast preprocessing + `pytesseract` OCR fallback for scanned images.
   - **Resilience**: Comprehensive error handling for corrupted, empty, or password-protected PDFs.

3. **Intelligent Resume Parsing**:
   - Google Gemini AI parses resumes into structured JSON (`name`, `email`, `phone`, `summary`, `skills`, `education`, `experience`, `projects`, `certifications`).
   - Bulletproof regex & heuristic fallback parser ensures 100% offline functionality if Gemini API key is missing.

4. **Dynamic Profile Scoring**:
   - Real calculated profile completeness score (0-100%) based on weighted criteria (Contact: 15, Summary: 10, Skills: 15, Education: 15, Experience: 15, Projects: 15, Certifications: 10, Quality bonus: 5).

5. **ATS Compatibility & Job Fit Analyzer**:
   - Real-time comparison of candidate resumes against job descriptions.
   - Calculates ATS match percentage (0-100%).
   - Identifies **matched skills**, **missing skills**, **matched strategic keywords**, and **missing keywords**.
   - Generates actionable recruiter insights and bullet-point improvements.

6. **Context-Aware AI Career Coach**:
   - Interactive chat assistant with context of the candidate's active resume.
   - Rewrites bullet points in the **STAR format** (Situation, Task, Action, Result) with metrics.
   - Mock interview questions and technical upskilling roadmaps.

7. **Resume Management**:
   - List all uploaded resumes, inspect full parsed structured records in interactive modals, download original PDFs, or delete resumes.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, Pydantic v2
- **Database**: PostgreSQL (with automatic zero-config SQLite fallback for local development)
- **AI**: Google Gemini API (`gemini-2.5-flash` / `gemini-1.5-flash`) + Intelligent Heuristic Fallback
- **PDF & OCR**: PyMuPDF (`pymupdf`), pytesseract, Pillow
- **Authentication**: JWT (`pyjwt`), Password Hashing (`bcrypt`)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (Zero npm dependencies, lightning fast)

---

## 🚀 Quickstart Guide

### 1. Clone & Install Dependencies

```bash
cd AI-Resume-Analyzer
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_analyzer
SECRET_KEY=resumelab-super-secret-jwt-signing-key-production-2026
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Optional: Google Gemini API Key (get free key at https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Tesseract OCR path (if not in system PATH)
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

> **Note**: If PostgreSQL is not running locally, the application automatically falls back to local SQLite (`sqlite:///./resume_analyzer.db`) without crashing.

### 3. Run the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the Web App

Open your browser and visit:
- **Web UI**: [http://localhost:8000/login.html](http://localhost:8000/login.html)
- **Interactive API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📁 Project Architecture

```
AI-Resume-Analyzer/
├── app/
│   ├── main.py                 # FastAPI application & routing
│   ├── dependencies.py         # Auth & Database dependencies
│   ├── api/
│   │   ├── auth.py             # Signup, Login, Me endpoints
│   │   ├── resume.py           # Upload, list, get, delete, download
│   │   ├── ats.py              # ATS matching & job analysis
│   │   └── chat.py             # Career assistant chat
│   ├── services/
│   │   ├── pdf_service.py      # PyMuPDF text extractor
│   │   ├── ocr_service.py      # Tesseract OCR pipeline
│   │   ├── resume_service.py   # Parsing coordinator & score calculator
│   │   ├── ats_service.py      # ATS scoring engine
│   │   └── gemini_service.py   # Gemini AI client & fallback parser
│   ├── database/
│   │   ├── models.py           # User & Resume SQLAlchemy models
│   │   ├── repository.py       # CRUD database access functions
│   │   └── session.py          # Engine & session management
│   ├── schemas/
│   │   └── schemas.py          # Pydantic validation schemas
│   └── core/
│       ├── config.py           # App settings
│       └── security.py         # JWT & bcrypt utilities
├── frontend/
│   ├── login.html              # Sign in page
│   ├── signup.html             # User registration
│   ├── dashboard.html          # Executive dashboard
│   ├── upload.html             # Resume PDF upload & structured view
│   ├── ats.html                # ATS job description scanner
│   ├── resumes.html            # Resume management & detail view
│   ├── chat.html               # AI Career Assistant
│   └── static/
│       ├── style.css           # Premium modern theme
│       ├── auth.js             # Auth client & token management
│       ├── dashboard.js        # Dashboard metrics & overview
│       ├── upload.js           # Drag & drop upload handler
│       ├── ats.js              # ATS analyzer client
│       ├── resumes.js          # Resume table & modal viewer
│       └── chat.js             # Chat assistant client
├── uploads/                    # Uploaded PDF resumes directory
├── requirements.txt
├── .env.example
└── README.md
```
