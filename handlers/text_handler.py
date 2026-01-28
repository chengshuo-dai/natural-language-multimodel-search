from handlers.base import FileHandler


class TextFileHandler(FileHandler):
    """Handler for plain text files."""

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        return [".txt"]

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract text from plain text files."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
