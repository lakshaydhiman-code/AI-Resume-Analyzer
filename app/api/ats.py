from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.schemas import ATSAnalyzeRequest, ATSAnalyzeResponse
from app.database import repository
from app.database.models import User
from app.dependencies import get_db, get_current_user
from app.services.ats_service import ATSService

router = APIRouter()

@router.post("/analyze", response_model=ATSAnalyzeResponse)
def analyze_ats(
    request: ATSAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compare a resume against a target job description and calculate ATS score,
    identifying matched & missing skills/keywords and actionable suggestions.
    """
    # 1. Fetch requested resume or fall back to latest
    if request.resume_id:
        resume = repository.get_resume_by_id(db, request.resume_id, current_user.id)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The specified resume was not found."
            )
    else:
        resume = repository.get_latest_resume(db, current_user.id)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No resume found for your account. Please upload a resume first before running an ATS check."
            )

    try:
        analysis_result = ATSService.evaluate_match(
            resume_text=resume.extracted_text,
            resume_data=resume.parsed_data or {},
            job_description=request.job_description
        )
        analysis_result["resume_id"] = resume.id
        analysis_result["resume_file_name"] = resume.file_name
        return analysis_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ATS analysis failed: {str(e)}")
