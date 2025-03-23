from threading import Lock

import numpy as np
import rich
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer


class SBertModel:
    """
    This SBertModel can be used to get the embedding of a text. It's a singleton class.
    """

    _lock = Lock()
    _instance = None

    @classmethod
    def _get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if SBertModel._instance is None:  # Double check locking
                    rich.print("[yellow]Loading SBertModel...[/yellow]")
                    SBertModel._instance = {
                        "model": SentenceTransformer("all-MiniLM-L6-v2"),
                        "tokenizer": AutoTokenizer.from_pretrained(
                            "sentence-transformers/all-MiniLM-L6-v2"
                        ),
                    }
        return SBertModel._instance

    @classmethod
    def get_embedding(cls, text: str, token_limit=512) -> np.ndarray:
        # TODO: Implement the token limit
        instance = cls._get_instance()
        return instance["model"].encode(text)

    @classmethod
    def get_dimension(cls):
        instance = cls._get_instance()
        model = instance["model"]
        return model.encode("random").shape[0]
