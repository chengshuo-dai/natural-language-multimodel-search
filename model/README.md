# Model Architecture

This directory contains lazy-loading model classes that implement the singleton pattern with animated loading indicators.

## Architecture Overview

### BaseModel (Abstract Base Class)
- **Location**: `model/base_model.py`
- **Purpose**: Provides the common singleton pattern with lazy loading and animated status indicators
- **Features**:
  - Automatic singleton instance management
  - Rich console status indicators during loading
  - Abstract method `_load_model()` that subclasses must implement
  - Public `get_instance()` method for accessing the model

### Model Classes

#### SBertModel
- **Purpose**: Text embedding using Sentence Transformers
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **API**: 
  - `get_embedding(text: str) -> np.ndarray`
  - `get_dimension() -> int`

#### WhisperModel  
- **Purpose**: Audio transcription using OpenAI Whisper
- **Model**: `base` (configurable)
- **API**: `transcribe(audio_path: str) -> dict`

#### BlipModel
- **Purpose**: Image captioning using BLIP
- **Model**: `Salesforce/blip-image-captioning-base`
- **API**: `generate_caption(image: Image.Image) -> str`

## Usage Examples

```python
# Text embedding
embedding = SBertModel.get_embedding("Hello world")
dimension = SBertModel.get_dimension()

# Audio transcription  
transcription = WhisperModel.transcribe("audio.mp3")

# Image captioning
caption = BlipModel.generate_caption(image)
```

## Benefits

1. **🚀 Lazy Loading**: Models only load when first needed
2. **🎨 Animated Loading**: Rich spinners show loading progress
3. **💾 Memory Efficient**: Singleton pattern ensures only one instance per model
4. **🔧 Maintainable**: Common code in BaseModel, specific logic in subclasses
5. **⚡ Better UX**: Users see loading progress instead of frozen terminal

## Adding New Models

To add a new model:

1. Create a new class inheriting from `BaseModel`
2. Set the `_MODEL_NAME` class variable
3. Implement the `_load_model()` method
4. Add your specific API methods

Example:
```python
class MyNewModel(BaseModel):
    _MODEL_NAME = "my-model-name"
    
    @classmethod
    def _load_model(cls):
        return load_my_model(cls._MODEL_NAME)
    
    @classmethod
    def my_method(cls, input_data):
        model = cls.get_instance()
        return model.process(input_data)
``` 