import pytesseract
from pdf2image import convert_from_path

from handlers.base import FileHandler


class PDFFileHandler(FileHandler):
    """Handler for PDF files."""

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        return [".pdf"]

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract text from PDF files using OCR."""
        # Convert PDF pages to images
        pages = convert_from_path(file_path)

        # Extract text from each page using OCR
        pdf_page_texts = [
            pytesseract.image_to_string(page.convert("RGB")) for page in pages
        ]

        # Join all page texts
        return "\n".join(pdf_page_texts)
