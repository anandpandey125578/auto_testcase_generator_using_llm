from pathlib import Path

import logging

import pdfplumber
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract


logger = logging.getLogger(__name__)


def _extract_pdf_with_pdfplumber(file_path):
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def _extract_pdf_with_pypdf2(file_path):
    text_parts = []
    reader = PdfReader(file_path)
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def extract_text_from_pdf(file_path):
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError("PDF file not found.")

    try:
        text = _extract_pdf_with_pdfplumber(file_path)
        if text:
            return text
    except Exception as exc:  # noqa: BLE001
        logger.exception("pdfplumber extraction failed: %s", exc)

    try:
        text = _extract_pdf_with_pypdf2(file_path)
        if text:
            return text
    except Exception as exc:  # noqa: BLE001
        logger.exception("PyPDF2 extraction failed: %s", exc)

    raise ValueError("No text extracted from PDF.")


def extract_text_from_image(file_path):
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError("Image file not found.")

    try:
        with Image.open(file_path) as image:
            text = pytesseract.image_to_string(image)
    except Exception as exc:  # noqa: BLE001
        logger.exception("OCR failed: %s", exc)
        raise ValueError("OCR failed for image.") from exc

    if not text or not text.strip():
        raise ValueError("No text extracted from image.")

    return text.strip()


def extract_text(pdf_paths=None, image_paths=None):
    pdf_list = []
    if isinstance(pdf_paths, (str, Path)):
        pdf_list = [pdf_paths]
    elif pdf_paths:
        pdf_list = list(pdf_paths)

    image_list = []
    if isinstance(image_paths, (str, Path)):
        image_list = [image_paths]
    elif image_paths:
        image_list = list(image_paths)

    text_blocks = []
    errors = []

    for pdf_path in pdf_list:
        try:
            text = extract_text_from_pdf(pdf_path)
            name = Path(pdf_path).name
            text_blocks.append(f"PDF: {name}\n{text}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"PDF extraction failed: {exc}")

    for index, image_path in enumerate(image_list, start=1):
        try:
            text = extract_text_from_image(image_path)
            name = Path(image_path).name
            text_blocks.append(f"Image {index}: {name}\n{text}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Image extraction failed: {exc}")

    merged_text = "\n\n".join(text_blocks).strip()
    if not merged_text:
        if errors:
            raise ValueError("; ".join(errors))
        raise ValueError("No text extracted from inputs.")

    return merged_text
