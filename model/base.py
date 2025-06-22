from abc import ABC, abstractmethod

from rich.console import Console


class Model(ABC):
    """
    Base class for lazy-loading models with animated loading indicators.
    Implements the singleton pattern with rich console status indicators.
    """

    _instance = None
    _MODEL_NAME = None  # Must be set by subclasses

    @classmethod
    def _get_instance(cls):
        """
        Get the singleton instance, loading it with animation if needed.
        """
        if cls._instance is None:
            if cls._MODEL_NAME is None:
                raise NotImplementedError(
                    f"Subclass {cls.__name__} must set _MODEL_NAME"
                )

            console = Console()
            model_display_name = cls.__name__.replace("Model", "")
            with console.status(
                f"[yellow]Loading {model_display_name}...", spinner="dots"
            ):
                cls._instance = cls._load_model()
        return cls._instance

    @classmethod
    @abstractmethod
    def _load_model():
        """
        Abstract method that subclasses must implement to load their specific model.
        This method should return the loaded model instance.
        """
        pass

    @classmethod
    def get_instance(cls):
        """
        Public method to get the model instance.
        """
        return cls._get_instance()
