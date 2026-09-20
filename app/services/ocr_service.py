import os
import shutil
import logging
from pathlib import Path
from typing import Optional
import pymupdf
try:
    from PIL import Image, ImageOps, ImageEnhance
    import pytesseract
    _PIL_AVAILABLE = True
except ImportError as e:
    _PIL_AVAILABLE = False
    logger_temp = logging.getLogger('resumelab.ocr_service')
    logger_temp.warning(f"PIL could not be imported. Image enhancement will be disabled.")

from app.core.config import settings

logger = logging.getLogger('resumelab.ocr_service')

class OCRService:
    _tesseract_cmd: Optional[str] = None
    _configured: Optional[bool] = None

    @classmethod
    def _find_and_configure_tesseract(cls) -> bool:
        if cls._configured is not None:
            return cls._configured

        if settings.TESSERACT_CMD and os.path.exists(settings.TESSERACT_CMD):
            cls._tesseract_cmd = settings.TESSERACT_CMD
            cls._configured = True
            return True

        tesseract_in_path = shutil.which('tesseract')
        if tesseract_in_path:
            cls._tesseract_cmd = tesseract_in_path
            cls._configured = True
            return True

        common_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            os.path.expandvars(r'%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe'),
            os.path.expandvars(r'%USERPROFILE%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe')
        ]
        for p in common_paths:
            if os.path.exists(p):
                cls._tesseract_cmd = p
                cls._configured = True
                return True

        cls._configured = False
        return False

    @classmethod
    def is_available(cls) -> bool:
        return cls._find_and_configure_tesseract()

    @classmethod
    def extract_text_from_pdf(cls, file_path: Path, dpi: int = 250) -> str:
        if not cls.is_available():
            logger.warning('OCR requested but Tesseract is not configured or installed.')
            raise ValueError(
                'OCR is not configured correctly. The PDF appears to be a scanned image, '
                'but Tesseract OCR is not installed or not in PATH.'
            )

        try:
            doc = pymupdf.open(str(file_path))
        except Exception as e:
            raise ValueError(f'Could not open PDF for OCR: {e}')

        if doc.is_encrypted:
            doc.close()
            raise ValueError('Password-protected PDFs cannot be read.')

        page_texts = []
        scale = dpi / 72.0
        matrix = pymupdf.Matrix(scale, scale)

        import tempfile
        import subprocess

        for page_idx in range(len(doc)):
            try:
                page = doc.load_page(page_idx)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
                    tmp_img_path = tmp_img.name
                
                pix.save(tmp_img_path)
                
                # Use subprocess to bypass PIL dependency
                out_prefix = tmp_img_path + "_out"
                
                # tesseract img.png out_prefix -l eng --psm 6
                cmd = [
                    cls._tesseract_cmd,
                    tmp_img_path,
                    out_prefix,
                    "-l", "eng",
                    "--psm", "6"
                ]
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                out_txt = out_prefix + ".txt"
                if os.path.exists(out_txt):
                    with open(out_txt, 'r', encoding='utf-8') as f:
                        ocr_text = f.read()
                    if ocr_text.strip():
                        page_texts.append(ocr_text.strip())
                    os.remove(out_txt)
                
                if os.path.exists(tmp_img_path):
                    os.remove(tmp_img_path)
                    
            except Exception as e:
                logger.error(f'Error during OCR on page {page_idx}: {e}')
                if 'tmp_img_path' in locals() and os.path.exists(tmp_img_path):
                    os.remove(tmp_img_path)
                if 'out_txt' in locals() and os.path.exists(out_txt):
                    os.remove(out_txt)

        doc.close()

        combined_text = '\n\n'.join(page_texts).strip()
        if not combined_text:
            raise ValueError('This scanned resume could not be read clearly. Please ensure the scan is readable.')

        return combined_text
