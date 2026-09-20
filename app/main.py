import os
import logging
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import auth, resume, ats, chat

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("resumelab")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade AI Resume Analyzer, ATS Matcher, and Career Coach"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(resume.router, prefix="/resume", tags=["Resume Management"])
app.include_router(ats.router, prefix="/ats", tags=["ATS Analysis"])
app.include_router(chat.router, prefix="/chat", tags=["Career Assistant Chat"])

# Static Files
static_dir = settings.FRONTEND_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Custom exception handler for clean error responses
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )

# Frontend Page Routes
@app.get("/")
async def root():
    """Root redirect to dashboard if authenticated, or login."""
    return RedirectResponse(url="/dashboard.html")

@app.get("/{page_name}.html")
async def serve_html_page(page_name: str):
    """Serve specific frontend HTML page."""
    html_file = settings.FRONTEND_DIR / f"{page_name}.html"
    if html_file.exists():
        return FileResponse(str(html_file))
    return JSONResponse(status_code=404, content={"detail": f"Page '{page_name}.html' not found"})

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.PROJECT_NAME, "version": settings.VERSION}
