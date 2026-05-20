"""Configuration module for Task 3."""
import os
import sys
from pathlib import Path

# Add parent directory to path to find config from task2
sys.path.insert(0, str(Path(__file__).parent.parent / "task2"))

from config import GEMINI_API_KEY, MODEL_NAME, MAX_TOKENS

__all__ = ["GEMINI_API_KEY", "MODEL_NAME", "MAX_TOKENS"]
