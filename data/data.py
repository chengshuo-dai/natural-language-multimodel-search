import dataclasses
from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass
class File:
    filename: str
    created: float
    path: str
    size: int
    extension: str

    @classmethod
    def from_elasticsearch_source(cls, source: dict) -> "File":
        """Create a File object from Elasticsearch response source data."""
        return cls(
            filename=source["filename"],
            created=source["created"],
            path=source["metadata"]["path"],
            size=source["metadata"]["size"],
            extension=source["metadata"]["extension"],
        )


@dataclass
class Document:
    filename: str
    text: str
    extension: str
    created: datetime
    size: int
    path: str
    embedding: np.ndarray | None = None

    def _get_metadata(self) -> dict:
        return {
            "filename": self.filename,
            "extension": self.extension,
            "created": self.created,
            "size": self.size,
            "path": self.path,
        }

    def to_index_body(self) -> dict:
        if self.embedding is None:
            raise ValueError("Embedding is not set yet.")

        return {
            "filename": self.filename,
            "extension": self.extension,
            "text": self.text,
            "created": self.created,
            "embedding": self.embedding.tolist(),
            "metadata": self._get_metadata(),
        }


@dataclass
class NLSResult:
    result_type: str  # "answer" or "search"
    # list of filenames for search results or sources for answers
    # NOTE: we don't use list[File] because we want to keep the result type simple enough as the output of tools
    # so that it's easier for LLM to parse
    # we keep a mapping from filename to File object separately.
    files: list[str]
    answer: str  # answer for question, empty string if result_type is "search"
