import logging
from pathlib import Path
from typing import Tuple, Dict, Any
from app.services.pdf_service import PDFService
from app.services.ocr_service import OCRService
from app.services.gemini_service import GeminiService

logger = logging.getLogger("resumelab.resume_service")

class ResumeService:
    @classmethod
    def calculate_profile_score(cls, parsed_data: Dict[str, Any], text_length: int) -> int:
        score = 0
        if parsed_data.get("name") and len(str(parsed_data["name"]).strip()) > 1:
            score += 5
        if parsed_data.get("email") and "@" in str(parsed_data["email"]):
            score += 5
        if parsed_data.get("phone") and len(str(parsed_data["phone"]).strip()) >= 7:
            score += 5

        summary = str(parsed_data.get("summary", "")).strip()
        word_count = len(summary.split())
        if word_count >= 25:
            score += 10
        elif word_count >= 8:
            score += 5

        skills = parsed_data.get("skills", [])
        if isinstance(skills, list):
            if len(skills) >= 8:
                score += 15
            elif len(skills) >= 4:
                score += 10
            elif len(skills) >= 1:
                score += 5

        education = parsed_data.get("education", [])
        if isinstance(education, list) and len(education) > 0:
            score += 15

        experience = parsed_data.get("experience", [])
        if isinstance(experience, list) and len(experience) > 0:
            score += 15

        projects = parsed_data.get("projects", [])
        if isinstance(projects, list) and len(projects) > 0:
            score += 15

        certifications = parsed_data.get("certifications", [])
        if isinstance(certifications, list) and len(certifications) > 0:
            score += 10

        if text_length >= 350 and "@" in str(parsed_data.get("email", "")):
            score += 5

        return min(100, max(0, score))

    @classmethod
    def process_and_parse_resume(cls, file_path: Path, original_filename: str) -> Tuple[str, Dict[str, Any], int]:
        try:
            normal_text, page_count, metadata = PDFService.extract_text(file_path)
        except Exception as e:
            raise ValueError(f"Could not read this PDF. {str(e)}")

        final_text = normal_text

        if not PDFService.is_text_sufficient(normal_text, min_chars=100):
            logger.info(f"Normal text length is {len(normal_text.strip())} chars; attempting OCR for {original_filename}...")
            try:
                ocr_text = OCRService.extract_text_from_pdf(file_path)
                if len(ocr_text.strip()) > len(normal_text.strip()):
                    final_text = ocr_text
            except Exception as e:
                logger.warning(f"OCR attempt error: {e}")
                if len(normal_text.strip()) < 20:
                    raise ValueError(str(e))

        if len(final_text.strip()) < 20:
            raise ValueError("Could not read this PDF. Please upload a valid resume PDF with readable text.")

        parsed_data = GeminiService.parse_resume(final_text)
        profile_score = cls.calculate_profile_score(parsed_data, len(final_text))

        return final_text, parsed_data, profile_score
