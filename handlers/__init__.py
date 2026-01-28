from .audio_handler import AudioFileHandler
from .base import FileHandler
from .image_handler import ImageFileHandler
from .pdf_handler import PDFFileHandler
from .text_handler import TextFileHandler
from .video_handler import VideoFileHandler

# Build extension-to-handler mapping (single source of truth)
EXTENSION_TO_HANDLER = {}
for handler in [
    TextFileHandler,
    ImageFileHandler,
    PDFFileHandler,
    AudioFileHandler,
    VideoFileHandler,
]:
    for ext in handler.get_supported_extensions():
        EXTENSION_TO_HANDLER[ext] = handler

__all__ = [
    "AudioFileHandler",
    "FileHandler",
    "ImageFileHandler",
    "PDFFileHandler",
    "TextFileHandler",
    "VideoFileHandler",
    "EXTENSION_TO_HANDLER",
]
