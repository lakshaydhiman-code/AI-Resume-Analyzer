import os
import shutil
import time
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.schemas.schemas import ResumeUploadResponse, ResumeSummaryResponse, ResumeDetailResponse
from app.database import repository
from app.database.models import User
from app.dependencies import get_db, get_current_user
from app.services.resume_service import ResumeService
from app.core.config import settings

router = APIRouter()

@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and analyze resume PDF:
    1. Validates file is PDF
    2. Saves file safely to user uploads
    3. Extracts text via PyMuPDF (with OCR fallback for scanned resumes)
    4. Parses structured fields using AI / fallback
    5. Calculates profile score
    6. Persists to database
    7. Returns full structured response
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was uploaded.")

    filename_lower = file.filename.lower()
    if not filename_lower.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported. Please upload a valid .pdf resume."
        )

    # Sanitize filename and create unique storage path
    safe_name = os.path.basename(file.filename).replace(" ", "_")
    timestamp = int(time.time() * 1000)
    stored_filename = f"user_{current_user.id}_{timestamp}_{safe_name}"
    file_path = settings.UPLOAD_DIR / stored_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    # Process and parse resume
    try:
        extracted_text, parsed_data, profile_score = ResumeService.process_and_parse_resume(
            file_path=file_path,
            original_filename=file.filename
        )
    except ValueError as e:
        # Clean up failed file upload
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception:
                pass
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Resume processing failed: {str(e)}")

    # Persist in database
    resume_record = repository.save_resume(
        db=db,
        user_id=current_user.id,
        file_name=file.filename,
        file_path=str(file_path),
        extracted_text=extracted_text,
        parsed_data=parsed_data,
        profile_score=profile_score
    )

    return {
        "success": True,
        "resume_id": resume_record.id,
        "profile_score": resume_record.profile_score,
        "file_name": resume_record.file_name,
        "resume": parsed_data
    }

@router.get("/latest", response_model=ResumeDetailResponse)
def get_latest_resume(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the single most recent resume for the authenticated user."""
    resume = repository.get_latest_resume(db, current_user.id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resumes found for your account. Please upload one first."
        )
    return resume

@router.get("/list", response_model=List[ResumeSummaryResponse])
def get_user_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve list of all uploaded resumes for current user."""
    resumes = repository.get_user_resumes(db, current_user.id)
    results = []
    for r in resumes:
        data = r.parsed_data or {}
        skills = data.get("skills", [])
        name = data.get("name", "")
        results.append({
            "id": r.id,
            "file_name": r.file_name,
            "profile_score": r.profile_score,
            "created_at": r.created_at,
            "skills_count": len(skills) if isinstance(skills, list) else 0,
            "candidate_name": name
        })
    return results

@router.get("/{resume_id}", response_model=ResumeDetailResponse)
def get_resume_by_id(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a specific resume record by ID (owned by current user)."""
    resume = repository.get_resume_by_id(db, resume_id, current_user.id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or you do not have permission to view it."
        )
    return resume

@router.delete("/{resume_id}")
def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a resume by ID."""
    resume = repository.get_resume_by_id(db, resume_id, current_user.id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or you do not have permission to delete it."
        )

    # Delete physical file
    if resume.file_path and os.path.exists(resume.file_path):
        try:
            os.remove(resume.file_path)
        except Exception:
            pass

    deleted = repository.delete_resume(db, resume_id, current_user.id)
    return {"success": deleted, "message": "Resume deleted successfully."}

@router.get("/{resume_id}/download")
def download_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download the original uploaded PDF file."""
    resume = repository.get_resume_by_id(db, resume_id, current_user.id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or unauthorized access."
        )

    if not resume.file_path or not os.path.exists(resume.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original PDF file is no longer available on disk."
        )

    return FileResponse(
        path=resume.file_path,
        filename=resume.file_name,
        media_type="application/pdf"
    )
