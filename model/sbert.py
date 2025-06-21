import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

from model.base_model import BaseModel


class SBertModel(BaseModel):
    """
    This SBertModel can be used to get the embedding of a text. It's a singleton class.
    """

    _MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    @classmethod
    def _load_model(cls):
        """Load the SBert model and tokenizer."""
        return {
            "model": SentenceTransformer(cls._MODEL_NAME),
            "tokenizer": AutoTokenizer.from_pretrained(cls._MODEL_NAME),
        }

    @classmethod
    def get_embedding(cls, text: str, token_limit=512) -> np.ndarray:
        # TODO: Implement the token limit
        instance = cls.get_instance()
        return instance["model"].encode(text)

    @classmethod
    def get_dimension(cls):
        instance = cls.get_instance()
        model = instance["model"]
        return model.encode("random").shape[0]
