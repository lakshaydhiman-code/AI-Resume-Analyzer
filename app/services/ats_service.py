import logging
from typing import Dict, Any
from app.services.gemini_service import GeminiService

logger = logging.getLogger("resumelab.ats_service")

class ATSService:
    @classmethod
    def evaluate_match(cls, resume_text: str, resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        if not job_description or len(job_description.strip()) < 20:
            raise ValueError("Please provide a comprehensive job description (at least 20 characters).")

        return GeminiService.analyze_ats(
            resume_text=resume_text,
            resume_data=resume_data,
            job_description=job_description
        )
