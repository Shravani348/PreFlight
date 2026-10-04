"""Configuration for AI/ML module."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AIConfig:
    """AI module configuration settings."""

    api_key: str = os.getenv("AI_API_KEY", "")
    model_name: str = os.getenv("AI_MODEL_NAME", "default-vision-model")
    request_timeout: int = int(os.getenv("AI_REQUEST_TIMEOUT", "30"))


config = AIConfig()
