import whisper

from model.base import Model


class WhisperModel(Model):
    """
    This WhisperModel can be used to transcribe audio files. It's a singleton class.
    """

    _MODEL_NAME = "base"

    @classmethod
    def _load_model(cls):
        """Load the Whisper model."""
        return whisper.load_model(cls._MODEL_NAME)

    @classmethod
    def transcribe(cls, audio_path: str) -> dict:
        """
        Transcribe an audio file using Whisper.

        Args:
            audio_path: Path to the audio file

        Returns:
            Dictionary containing transcription results
        """
        model = cls.get_instance()
        return model.transcribe(audio_path)
