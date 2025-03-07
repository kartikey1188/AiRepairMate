from backend.app.api import *
from langchain.agents import tool
from langchain_google_genai import ChatGoogleGenerativeAI
import base64
import re

MODEL_NAME = "gemini-2.0-flash-exp-audio"

def clean_text(text):
    """Cleans LLM-generated text while preserving actual content."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Remove bold (**bold** → bold)
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # Remove italics (*italics* → italics)
    text = re.sub(r"_(.*?)_", r"\1", text)  # Remove underlines (_underline_ → underline)
    text = re.sub(r"`(.*?)`", r"\1", text)  # Remove inline code (`code` → code)
    text = re.sub(r"<.*?>", "", text)  # Remove HTML tags (if any)
    return text.strip()

@tool
def describe_audio(audio: bytes):
    """Takes an audio file as input and returns a detailed description using Gemini-2.0-Flash-Exp-Audio."""
    
    encoded_audio = base64.b64encode(audio).decode("utf-8")
    
    model = ChatGoogleGenerativeAI(model=MODEL_NAME)
    
    response = model.invoke([
        {"type": "text", "text": "Describe the audio content in detail, including speech, sounds, and background noise."},
        {"type": "audio", "audio": encoded_audio}
    ])
    
    return clean_text(response.content) if response else "Could not generate description."
