import re
from datetime import datetime
from typing import Optional, List, Any, Dict, Union
from pydantic import BaseModel, EmailStr, Field, field_validator

# ================= AUTH SCHEMAS =================
class UserSignup(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full Name")
    email: EmailStr = Field(..., description="Valid Email Address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (min 6 chars)")
    confirm_password: str = Field(..., description="Password Confirmation")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

# ================= RESUME SCHEMAS =================
class ResumeParsedData(BaseModel):
    name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    summary: Optional[str] = ""
    skills: List[str] = Field(default_factory=list)
    education: List[Union[Dict[str, Any], str]] = Field(default_factory=list)
    experience: List[Union[Dict[str, Any], str]] = Field(default_factory=list)
    projects: List[Union[Dict[str, Any], str]] = Field(default_factory=list)
    certifications: List[Union[Dict[str, Any], str]] = Field(default_factory=list)

class ResumeUploadResponse(BaseModel):
    success: bool = True
    resume_id: int
    profile_score: int
    file_name: str
    resume: ResumeParsedData

class ResumeSummaryResponse(BaseModel):
    id: int
    file_name: str
    profile_score: int
    created_at: datetime
    skills_count: int = 0
    candidate_name: Optional[str] = ""

    class Config:
        from_attributes = True

class ResumeDetailResponse(BaseModel):
    id: int
    file_name: str
    extracted_text: str
    parsed_data: Dict[str, Any]
    profile_score: int
    created_at: datetime

    class Config:
        from_attributes = True

# ================= ATS SCHEMAS =================
class ATSAnalyzeRequest(BaseModel):
    job_description: str = Field(..., min_length=20, description="Job Description text")
    resume_id: Optional[int] = Field(None, description="Specific resume ID to analyze, or latest if omitted")

class ATSAnalyzeResponse(BaseModel):
    ats_score: int = Field(..., ge=0, le=100, description="ATS Compatibility Score percentage")
    job_title_detected: Optional[str] = "Job Role"
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    summary_assessment: str = ""
    resume_id: Optional[int] = None
    resume_file_name: Optional[str] = None

# ================= CHAT SCHEMAS =================
class ChatMessage(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt or question")
    resume_id: Optional[int] = Field(None, description="Resume ID for context (or latest if omitted)")
    history: Optional[List[ChatMessage]] = Field(default_factory=list)

class ChatMessageResponse(BaseModel):
    reply: str
    resume_used: Optional[Dict[str, Any]] = None
