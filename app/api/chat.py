from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.schemas import ChatMessageRequest, ChatMessageResponse
from app.database import repository
from app.database.models import User
from app.dependencies import get_db, get_current_user
from app.services.gemini_service import GeminiService

router = APIRouter()

@router.post("/message", response_model=ChatMessageResponse)
def chat_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI Career & Resume Assistant chat endpoint.
    Answers candidate questions with contextual knowledge of their uploaded resume.
    """
    # Find resume context
    resume_record = None
    if request.resume_id:
        resume_record = repository.get_resume_by_id(db, request.resume_id, current_user.id)
    if not resume_record:
        resume_record = repository.get_latest_resume(db, current_user.id)

    resume_context = {}
    if resume_record and resume_record.parsed_data:
        resume_context = resume_record.parsed_data
    else:
        resume_context = {
            "name": current_user.name,
            "email": current_user.email,
            "skills": [],
            "summary": "",
            "experience": [],
            "education": []
        }

    history_dicts = [{"role": h.role, "content": h.content} for h in (request.history or [])]

    try:
        reply = GeminiService.chat_career_assistant(
            user_message=request.message,
            resume_context=resume_context,
            history=history_dicts
        )
        return {
            "reply": reply,
            "resume_used": {
                "id": resume_record.id if resume_record else None,
                "file_name": resume_record.file_name if resume_record else None
            } if resume_record else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat assistant failed: {str(e)}")
