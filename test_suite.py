import os
import sys
import io
import time
import pymupdf
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal, create_tables
from app.database.models import User, Resume

client = TestClient(app)

def create_sample_resume_pdf(candidate_name="Jane Doe", email="jane.doe@techcorp.com", phone="+1-555-0199"):
    """Create a valid in-memory PDF resume using PyMuPDF."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842) # A4 size

    text = f"""
{candidate_name}
Email: {email} | Phone: {phone} | Location: San Francisco, CA
LinkedIn: linkedin.com/in/janedoe | GitHub: github.com/janedoe

PROFESSIONAL SUMMARY
Senior Software Engineer with 6+ years of experience designing and architecting high-throughput distributed microservices, cloud-native backends, and data pipelines. Proven track record in optimizing database performance, implementing CI/CD automation, and mentoring engineering teams.

TECHNICAL SKILLS
- Languages: Python, JavaScript, TypeScript, Go, SQL
- Frameworks: FastAPI, Django, Flask, React, Node.js, Express
- Databases: PostgreSQL, Redis, MongoDB, SQLAlchemy, Elasticsearch
- Cloud & DevOps: AWS, Docker, Kubernetes, CI/CD, GitHub Actions, Terraform, Linux
- Core Competencies: REST API, Microservices, System Design, Agile, Scrum, Unit Testing

WORK EXPERIENCE
Senior Backend Engineer | CloudScale Systems | 2022 - Present
- Architected and deployed 15+ asynchronous microservices using Python and FastAPI, handling 25,000+ requests per minute with 99.99% uptime.
- Optimized complex PostgreSQL queries and configured Redis caching layer, decreasing p99 API latency by 42%.
- Automated end-to-end CI/CD delivery pipelines using Docker and GitHub Actions, cutting release deployment cycles from 2 hours to 8 minutes.

Software Engineer | Apex Digital Solutions | 2019 - 2022
- Developed scalable RESTful backend services using Python, Django, and PostgreSQL for financial transaction workflows.
- Collaborated in an agile scrum team to engineer responsive user interfaces in React and TypeScript.
- Implemented comprehensive unit and integration test suites with Pytest, achieving 92% code coverage.

EDUCATION
Bachelor of Science in Computer Science | Stanford University | 2015 - 2019
GPA: 3.85 / 4.0 | Honors in Distributed Systems

KEY PROJECTS
- Real-Time AI Event Router: High-performance stream processor built with Python, Kafka, and Redis caching.
- Cloud Infrastructure Deployer: Automated Terraform and Docker provisioning framework on AWS.

CERTIFICATIONS
- AWS Certified Solutions Architect - Associate
- Certified Kubernetes Administrator (CKA)
"""
    rect = pymupdf.Rect(40, 40, 555, 800)
    page.insert_textbox(rect, text, fontsize=10, fontname="helv")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def run_tests():
    print("=" * 60)
    print("RUNNING COMPLETE RESUMELAB TEST SUITE")
    print("=" * 60)

    # 1. Health Check
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] Health Check Passed")

    # Generate unique test email with valid domain
    test_email = f"testuser_{int(time.time())}@example.com"
    test_password = "SecurePassword123!"

    # 2. Signup
    signup_res = client.post("/auth/signup", json={
        "name": "Jane Doe",
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password
    })
    assert signup_res.status_code == 201, f"Signup failed: {signup_res.text}"
    user_data = signup_res.json()
    assert user_data["email"] == test_email
    print(f"[PASS] User Signup Passed: {user_data['name']} ({user_data['email']})")

    # 3. Prevent duplicate signup
    dup_res = client.post("/auth/signup", json={
        "name": "Jane Doe",
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password
    })
    assert dup_res.status_code == 400, "Duplicate signup was not blocked!"
    print("[PASS] Duplicate Prevention Passed")

    # 4. Login
    login_res = client.post("/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token_data = login_res.json()
    assert "access_token" in token_data
    auth_header = {"Authorization": f"Bearer {token_data['access_token']}"}
    print("[PASS] User Login & JWT Token Passed")

    # 5. Current User Profile
    me_res = client.get("/auth/me", headers=auth_header)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == test_email
    print("[PASS] Auth Me Profile Passed")

    # 6. Upload PDF Resume
    pdf_bytes = create_sample_resume_pdf()
    files = {
        "file": ("Jane_Doe_Resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    }
    upload_res = client.post("/resume/upload", headers=auth_header, files=files)
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    upload_data = upload_res.json()
    assert upload_data["success"] is True
    resume_id = upload_data["resume_id"]
    profile_score = upload_data["profile_score"]
    parsed_skills = upload_data["resume"]["skills"]
    print(f"[PASS] Resume PDF Upload & Parse Passed (ID: {resume_id}, Profile Score: {profile_score}%, Skills: {len(parsed_skills)})")
    assert profile_score >= 70, f"Score too low for complete resume: {profile_score}"
    assert len(parsed_skills) >= 5, f"Too few skills parsed: {parsed_skills}"

    # 7. Get Latest Resume
    latest_res = client.get("/resume/latest", headers=auth_header)
    assert latest_res.status_code == 200
    latest_data = latest_res.json()
    assert latest_data["id"] == resume_id
    print("[PASS] Get Latest Resume Passed")

    # 8. List User Resumes
    list_res = client.get("/resume/list", headers=auth_header)
    assert list_res.status_code == 200
    resumes_list = list_res.json()
    assert len(resumes_list) >= 1
    assert resumes_list[0]["id"] == resume_id
    print("[PASS] List Resumes Passed")

    # 9. Get Specific Resume
    detail_res = client.get(f"/resume/{resume_id}", headers=auth_header)
    assert detail_res.status_code == 200
    print("[PASS] Get Specific Resume Passed")

    # 10. Download Original Resume
    dl_res = client.get(f"/resume/{resume_id}/download", headers=auth_header)
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"
    print("[PASS] Download PDF Resume Passed")

    # 11. Run ATS Analysis
    job_description = """
    Lead Python Backend Engineer
    We are looking for a Senior Python Developer with deep experience in FastAPI, PostgreSQL, Redis, and Docker.
    Must have hands-on expertise in AWS, Microservices architecture, Kubernetes, CI/CD pipelines, and Unit Testing.
    Knowledge of Kafka, Elasticsearch, and Golang is a strong plus.
    """
    ats_res = client.post("/ats/analyze", headers=auth_header, json={
        "resume_id": resume_id,
        "job_description": job_description
    })
    assert ats_res.status_code == 200, f"ATS analysis failed: {ats_res.text}"
    ats_data = ats_res.json()
    assert ats_data["ats_score"] >= 60, f"ATS score unexpected: {ats_data['ats_score']}"
    assert len(ats_data["matched_skills"]) > 0, "No matched skills found"
    assert len(ats_data["improvement_suggestions"]) > 0, "No improvement suggestions generated"
    print(f"[PASS] ATS Analysis Passed (ATS Score: {ats_data['ats_score']}%, Matched: {len(ats_data['matched_skills'])}, Suggestions: {len(ats_data['improvement_suggestions'])})")

    # 12. AI Career Assistant Chat
    chat_res = client.post("/chat/message", headers=auth_header, json={
        "message": "Can you rewrite my first job bullet point using the STAR method?",
        "resume_id": resume_id
    })
    assert chat_res.status_code == 200, f"Chat assistant failed: {chat_res.text}"
    chat_data = chat_res.json()
    assert len(chat_data["reply"]) > 20
    print("[PASS] AI Career Coach Chat Passed")

    # 13. Multi-Tenant Security Check (User 2 cannot access User 1's resume)
    user2_email = f"user2_{int(time.time())}@example.com"
    signup2 = client.post("/auth/signup", json={
        "name": "User Two",
        "email": user2_email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    login2 = client.post("/auth/login", json={"email": user2_email, "password": "Password123!"})
    auth_header2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}

    # User 2 tries to access User 1's resume
    sec_res = client.get(f"/resume/{resume_id}", headers=auth_header2)
    assert sec_res.status_code == 404, "Security violation: User 2 accessed User 1's resume!"

    sec_del = client.delete(f"/resume/{resume_id}", headers=auth_header2)
    assert sec_del.status_code == 404, "Security violation: User 2 deleted User 1's resume!"
    print("[PASS] Multi-Tenant Security Isolation Passed")

    # 14. Delete Resume
    del_res = client.delete(f"/resume/{resume_id}", headers=auth_header)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify resume no longer exists
    del_check = client.get(f"/resume/{resume_id}", headers=auth_header)
    assert del_check.status_code == 404
    print("[PASS] Resume Deletion Passed")

    print("=" * 60)
    print("ALL 14 TEST SUITES PASSED FLAWLESSLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
