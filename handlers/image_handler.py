import pytesseract
from PIL import Image

from handlers.base import FileHandler
from model.blip_model import BlipModel


class ImageFileHandler(FileHandler):
    """Handler for image files (PNG, JPG, JPEG)."""

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        return [".png", ".jpg", ".jpeg"]

    @classmethod
    def get_required_models(cls):
        """Return list of model classes required by this handler."""
        return [BlipModel] + super().get_required_models()

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract text from images using BLIP captioning and OCR."""
        image = Image.open(file_path).convert("RGB")

        # Get image description using BLIP
        description = BlipModel.generate_caption(image)

        # Get text using OCR
        ocr_result = pytesseract.image_to_string(image)

        # Combine both results
        return f"{description}\n{ocr_result}"
