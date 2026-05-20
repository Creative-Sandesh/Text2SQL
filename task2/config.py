import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "Gemini 3.1 Flash-Lite")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")
