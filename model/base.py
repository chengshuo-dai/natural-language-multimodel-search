from abc import ABC, abstractmethod

import rich


class Model(ABC):
    _instance = None
    _MODEL_NAME: str = ""

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            model_display_name = cls.__name__.replace("Model", "")
            rich.print(f"[yellow]󰦖 Loading {model_display_name} model...[/yellow]")

            # actual loading the model from the disk
            cls._instance = cls._load_model()  # lazy loading + singleton pattern

            rich.print(
                f"[green] {model_display_name} model loaded successfully [/green]"
            )
        return cls._instance

    @classmethod
    @abstractmethod
    def _load_model(cls):
        pass
