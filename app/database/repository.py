from typing import Optional, List
from sqlalchemy.orm import Session
from app.database.models import User, Resume

def create_user(db: Session, name: str, email: str, password_hash: str) -> User:
    """Create and persist a new user."""
    user = User(
        name=name.strip(),
        email=email.strip().lower(),
        password_hash=password_hash
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieve user by unique email address."""
    return db.query(User).filter(User.email == email.strip().lower()).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Retrieve user by primary key ID."""
    return db.query(User).filter(User.id == user_id).first()

def save_resume(
    db: Session,
    user_id: int,
    file_name: str,
    file_path: str,
    extracted_text: str,
    parsed_data: dict,
    profile_score: int
) -> Resume:
    """Save a parsed resume record for the authenticated user."""
    resume = Resume(
        user_id=user_id,
        file_name=file_name,
        file_path=file_path,
        extracted_text=extracted_text,
        parsed_data=parsed_data,
        profile_score=profile_score
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume

def get_resume_by_id(db: Session, resume_id: int, user_id: int) -> Optional[Resume]:
    """Get a specific resume owned by user_id."""
    return db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()

def get_user_resumes(db: Session, user_id: int) -> List[Resume]:
    """Get all resumes uploaded by user_id in descending order of upload date."""
    return db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.created_at.desc()).all()

def get_latest_resume(db: Session, user_id: int) -> Optional[Resume]:
    """Get the single most recently uploaded resume for user_id."""
    return db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.created_at.desc()).first()

def delete_resume(db: Session, resume_id: int, user_id: int) -> bool:
    """Delete a resume owned by user_id."""
    resume = get_resume_by_id(db, resume_id, user_id)
    if not resume:
        return False
    db.delete(resume)
    db.commit()
    return True
