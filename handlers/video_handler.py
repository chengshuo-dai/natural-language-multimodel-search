from handlers.base import FileHandler
from model.video_model import VideoModel


class VideoFileHandler(FileHandler):
    """Handler for video files."""

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        return [".mp4", ".avi", ".mov", ".mkv", ".webm"]

    @classmethod
    def get_required_models(cls):
        """Return list of model classes required by this handler."""
        return [VideoModel] + super().get_required_models()

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract descriptive text from video files by analyzing visual content."""
        return VideoModel.analyze_video(file_path)
