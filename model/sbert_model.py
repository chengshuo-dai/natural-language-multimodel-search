import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

from model.base import Model


class SBertModel(Model):
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
    def get_embedding(cls, text: str, token_limit: int = 500) -> np.ndarray:
        """
        TODO: Respect token limit by splitting the text into chunks,
        embedding each chunk and then taking the average of the embeddings.
        """
        model = cls.get_instance()["model"]
        assert token_limit <= 512, "Token limit must be less than 512 for SBERT model."
        return model.encode(text, normalize_embeddings=True)

    @classmethod
    def get_dimension(cls) -> int:
        model = cls.get_instance()["model"]
        return model.encode("random text").shape[0]
