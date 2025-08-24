import cv2
import numpy as np
from PIL import Image

from model.base import Model
from model.blip_model import BlipModel


class VideoModel(Model):
    """
    Video processing model that extracts frames and generates descriptions.
    Uses BLIP model for frame captioning.
    """

    _MODEL_NAME = "video_processor"  # Not a real model, just a processor

    @classmethod
    def _load_model(cls):
        """Load dependencies - BLIP model will be loaded when needed."""
        return {"loaded": True}

    @classmethod
    def extract_frames(cls, video_path: str, max_frames: int = 10, interval: int = None) -> list[Image.Image]:
        """
        Extract frames from video file.
        
        Args:
            video_path: Path to video file
            max_frames: Maximum number of frames to extract
            interval: Frame interval (if None, evenly distribute frames)
            
        Returns:
            List of PIL Image objects
        """
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if interval is None:
            # Evenly distribute frames across video
            interval = max(1, total_frames // max_frames)
        
        frame_indices = list(range(0, min(total_frames, max_frames * interval), interval))
        
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convert to PIL Image
                pil_image = Image.fromarray(frame_rgb)
                frames.append(pil_image)
        
        cap.release()
        return frames

    @classmethod
    def analyze_video(cls, video_path: str, max_frames: int = 10) -> str:
        """
        Analyze video content by extracting frames and generating descriptions.
        
        Args:
            video_path: Path to video file
            max_frames: Maximum number of frames to analyze
            
        Returns:
            Combined description of video content
        """
        # Ensure this model is "loaded"
        cls.get_instance()
        
        # Extract frames
        frames = cls.extract_frames(video_path, max_frames)
        
        if not frames:
            return "No frames could be extracted from video"
        
        # Generate descriptions for each frame
        descriptions = []
        for i, frame in enumerate(frames):
            caption = BlipModel.generate_caption(frame)
            descriptions.append(f"Frame {i+1}: {caption}")
        
        # Combine descriptions
        video_description = f"Video analysis ({len(frames)} frames): " + " | ".join(descriptions)
        
        return video_description