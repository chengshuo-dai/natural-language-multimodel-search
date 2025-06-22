from model.whisper_model import WhisperModel
from processor.handlers.base import FileHandler


class AudioFileHandler(FileHandler):
    """Handler for audio files."""

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        return [".mp3"]

    @classmethod
    def get_required_models(cls):
        """Return list of model classes required by this handler."""
        return [WhisperModel] + super().get_required_models()

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract text from audio files using Whisper transcription."""
        result = WhisperModel.transcribe(file_path)
        return result["text"]
