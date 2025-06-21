from PIL import Image
from transformers import BlipForConditionalGeneration, BlipProcessor

from model.base_model import BaseModel


class BlipModel(BaseModel):
    """
    This BlipModel can be used to generate image captions. It's a singleton class.
    """

    _MODEL_NAME = "Salesforce/blip-image-captioning-base"

    @classmethod
    def _load_model(cls):
        """Load the BLIP model and processor."""
        return {
            "processor": BlipProcessor.from_pretrained(cls._MODEL_NAME),
            "model": BlipForConditionalGeneration.from_pretrained(cls._MODEL_NAME),
        }

    @classmethod
    def generate_caption(cls, image: Image.Image, max_new_tokens: int = 400) -> str:
        """
        Generate a caption for an image using BLIP.

        Args:
            image: PIL Image object
            max_new_tokens: Maximum number of tokens to generate

        Returns:
            Generated caption as string
        """
        instance = cls.get_instance()
        processor = instance["processor"]
        model = instance["model"]

        # Process the image
        inputs = processor(image, return_tensors="pt")

        # Generate caption
        out = model.generate(**inputs, max_new_tokens=max_new_tokens)

        # Decode the generated tokens
        caption = processor.decode(out[0], skip_special_tokens=True)

        return caption
