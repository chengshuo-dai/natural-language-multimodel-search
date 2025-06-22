from model import Model
from processor.handlers import (
    AudioFileHandler,
    FileHandler,
    ImageFileHandler,
    PDFFileHandler,
    TextFileHandler,
)


class FileHandlerRegistry:
    """Registry for file handlers with extension mapping."""

    _handlers: dict[str, type[FileHandler]] = {}

    @classmethod
    def register(cls, handler_class: type[FileHandler]):
        """Register a handler class."""
        for extension in handler_class.get_supported_extensions():
            if extension in cls._handlers:
                raise ValueError(
                    f"Extension {extension} is already handled by {cls._handlers[extension].__name__}"
                )
            cls._handlers[extension] = handler_class

    @classmethod
    def get_handler(cls, extension: str) -> type[FileHandler] | None:
        """Get handler for a specific extension."""
        return cls._handlers.get(extension.lower())

    @classmethod
    def can_handle(cls, extension: str) -> bool:
        """Check if an extension is supported."""
        return extension.lower() in cls._handlers

    @classmethod
    def load_required_models(cls, extensions: set[str]) -> None:
        """Load all required models for the given extensions (or all if None)."""
        # Inline the logic from get_required_models_for_extensions
        required_models = set()
        for extension in extensions:
            handler_class = cls.get_handler(extension)
            if handler_class:
                required_models.update(handler_class.get_required_models())

        # Load each model (they use singleton pattern, so this is safe)
        for model_class in required_models:
            model_class.get_instance()


def register_all_handlers():
    """Register all available file handlers."""
    handlers = [
        TextFileHandler,
        ImageFileHandler,
        PDFFileHandler,
        AudioFileHandler,
    ]

    for handler in handlers:
        FileHandlerRegistry.register(handler)


# Auto-register handlers when module is imported
register_all_handlers()
