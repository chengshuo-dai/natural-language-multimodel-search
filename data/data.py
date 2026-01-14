import dataclasses
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np


@dataclass
class Document:
    filename: str
    extension: str
    created: datetime
    size: int
    path: str
    text: str
    embedding: np.ndarray

    @classmethod
    def from_es_dict(cls, source: dict[str, Any]) -> "Document":
        """Create a Document object from Elasticsearch response source data."""
        return cls(
            filename=source["filename"],
            extension=source["extension"],
            created=datetime.fromisoformat(source["created"].replace("Z", "+00:00")),
            path=source["path"],
            size=source["size"],
            text=source["text"],
            embedding=np.array(source["embedding"]),
        )

    def to_es_dict(self) -> dict[str, Any]:
        """Convert Document to Elasticsearch index dict."""
        body = dataclasses.asdict(self)
        body["embedding"] = self.embedding.tolist()
        return body


@dataclass
class NLSResult:
    result_type: str  # "answer" or "search"
    # list of filenames for search results or sources for answers
    # NOTE: we don't use list[Document] because we want to keep the result type simple enough as the output of tools
    # so that it's easier for LLM to parse
    # we keep a mapping from filename to Document object separately.
    files: list[str]
    answer: str  # answer for question, empty string if result_type is "search"
