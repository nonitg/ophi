"""List the Gemini models this machine's key can call, so letters.MODEL can be set to one that exists.

Run: .venv/bin/python scripts/gemini-models.py
"""
from dotenv import load_dotenv

load_dotenv()

from google import genai  # noqa: E402  (after load_dotenv, which supplies GEMINI_API_KEY)

for m in sorted(genai.Client().models.list(), key=lambda m: m.name or ""):
    if "generateContent" in (m.supported_actions or []) and "embedding" not in (m.name or ""):
        print(f"{m.name:52} in={m.input_token_limit or '?':>9} out={m.output_token_limit or '?':>7}")
