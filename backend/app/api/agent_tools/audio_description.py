from backend.app.api import *
import google.generativeai as genai
import base64
import re
from dotenv import load_dotenv
import os

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def clean_text(text):
    """Cleans LLM-generated text while preserving actual content."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()

def describe_audio(audio: str):
    """Takes base64-encoded MP3 audio and uses Gemini to describe it."""

    audio_bytes = base64.b64decode(audio)

    model = genai.GenerativeModel("gemini-1.5-pro")  # audio input only supported here

    response = model.generate_content([
        "Describe the audio in detail. Identify the appliance or object involved, model if possible, and any technical issues or context. Break down the sounds or speech in a structured way.",
        {
            "mime_type": "audio/mpeg",
            "data": audio_bytes
        }
    ])

    return clean_text(response.text) if response and hasattr(response, "text") else "Could not generate description."
