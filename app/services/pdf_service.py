import os
import re
import logging
from pathlib import Path
from typing import Tuple, Dict, Any
import pymupdf

logger = logging.getLogger('resumelab.pdf_service')

class PDFService:
    @staticmethod
    def is_valid_pdf(file_path: Path) -> bool:
        if not file_path.exists() or file_path.stat().st_size == 0:
            return False
        try:
            with open(file_path, 'rb') as f:
                header = f.read(5)
                return header.startswith(b'%PDF-')
        except Exception:
            return False

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ''
        text = text.replace('\x00', ' ')
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        return text.strip()

    @classmethod
    def extract_text(cls, file_path: Path) -> Tuple[str, int, Dict[str, Any]]:
        if not cls.is_valid_pdf(file_path):
            raise ValueError('The uploaded file is not a valid PDF document.')

        try:
            doc = pymupdf.open(str(file_path))
        except Exception as e:
            logger.error(f'Error opening PDF {file_path}: {e}')
            raise ValueError('Could not read this PDF. The file may be corrupted.')

        if doc.is_encrypted:
            doc.close()
            raise ValueError('Password-protected PDFs cannot be read. Please upload an unencrypted PDF.')

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise ValueError('The uploaded PDF has no pages.')

        extracted_pages = []
        for page_idx in range(page_count):
            try:
                page = doc.load_page(page_idx)
                page_text = page.get_text('text')
                if page_text:
                    extracted_pages.append(page_text)
            except Exception as e:
                logger.warning(f'Error reading page {page_idx} from {file_path}: {e}')

        metadata = dict(doc.metadata or {})
        doc.close()

        full_raw_text = '\n\n'.join(extracted_pages)
        cleaned_text = cls.clean_text(full_raw_text)
        return cleaned_text, page_count, metadata

    @classmethod
    def is_text_sufficient(cls, text: str, min_chars: int = 100) -> bool:
        if not text:
            return False
        return len(text.strip()) >= min_chars
