import datetime
import os
from abc import ABC, abstractmethod

from data.data import Document
from model.base import Model
from model.sbert_model import SBertModel


class FileHandler(ABC):
    """Base class for file handlers that process different file types."""

    @classmethod
    @abstractmethod
    def get_supported_extensions(cls) -> list[str]:
        """Return list of file extensions this handler supports."""
        pass

    @classmethod
    @abstractmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract text content from the file."""
        pass

    @classmethod
    def get_required_models(cls) -> list[type[Model]]:
        """Return list of model classes required by this handler."""
        # Default: all handlers need SBert for embeddings
        return [SBertModel]

    @classmethod
    def process_file(cls, file_path: str) -> Document:
        """Process a file and return a Document object with embedding."""
        # Common processing logic
        filename = os.path.basename(file_path)
        extension = os.path.splitext(file_path)[1].lower()

        # Extract text using the specific handler
        text = cls.extract_text(file_path)

        # Generate embedding
        embedding = SBertModel.get_embedding(text)

        # Create and return document
        return Document(
            filename=filename,
            text=text,
            extension=extension,
            created_at=datetime.datetime.fromtimestamp(os.path.getmtime(file_path)),
            size=os.path.getsize(file_path),
            path=file_path,
            embedding=embedding,
        )
