import dataclasses
from datetime import datetime
from typing import Optional

import numpy as np


@dataclasses.dataclass
class Document:
    filename: str
    text: str
    created: datetime
    size: int
    extension: str
    embedding: Optional[np.ndarray] = None

    def _get_metadata(self) -> dict:
        return {
            "filename": self.filename,
            "created": self.created,
            "size": self.size,
            "extension": self.extension,
        }

    def to_index_body(self) -> dict:
        if self.embedding is None:
            raise ValueError("Embedding is not set yet.")

        return {
            "filename": self.filename,
            "extension": self.extension,
            "text": self.text,
            "created": self.created,
            "size": self.size,
            "embedding": self.embedding.tolist(),
            "metadata": self._get_metadata(),
        }
