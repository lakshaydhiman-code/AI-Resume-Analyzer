import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "AI Resume Analyzer / ResumeLab"
    VERSION: str = "1.0.0"
    
    # Secret key for JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "resumelab-super-secret-jwt-signing-key-production-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24h

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/resume_analyzer")
    SQLITE_FALLBACK_URL: str = "sqlite:///./resume_analyzer.db"

    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # OCR / Tesseract path
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "")

    # Upload directory
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    FRONTEND_DIR: Path = BASE_DIR / "frontend"

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
