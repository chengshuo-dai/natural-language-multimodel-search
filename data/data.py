import dataclasses
from datetime import datetime
from typing import Optional

import numpy as np


@dataclasses.dataclass
class Document:
    filename: str
    text: str
    extension: str
    created: datetime
    size: int
    path: str
    embedding: Optional[np.ndarray] = None

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
