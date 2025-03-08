from backend.app.api import *
from langchain.agents import tool
from langchain_google_genai import ChatGoogleGenerativeAI
import base64
import re

MODEL_NAME = "gemini-2.0-flash"

def clean_text(text):
    """Cleans LLM-generated text while preserving actual content."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Remove bold (**bold** → bold)
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # Remove italics (*italics* → italics)
    text = re.sub(r"_(.*?)_", r"\1", text)  # Remove underlines (_underline_ → underline)
    text = re.sub(r"`(.*?)`", r"\1", text)  # Remove inline code (`code` → code)
    text = re.sub(r"<.*?>", "", text)  # Remove HTML tags (if any)
    return text.strip()

def describe_audio(audio: str):
    """Takes an audio file as input and returns a detailed description using Gemini-2.0-Flash-Exp-Audio. Focus on finding and describing what the particular appliance/thing is, what its exact model is, and what the issue is."""
    
    model = ChatGoogleGenerativeAI(model=MODEL_NAME)
    
    response = model.invoke([
    {"role": "system", "content": "Describe the audio in detail, identifying the appliance or object it relates to. Analyze specific sounds, background noise, or spoken words that indicate the model, issue, or context of the audio. Provide a structured breakdown of the analysis."},
    {"role": "user", "content": f"Here is an audio file. Analyze it and describe the sounds, potential issues, and any identifiable appliance or object."},
    {"role": "user", "content": audio}  # Properly passing base64 audio
    ])
    
    return clean_text(response.content) if response else "Could not generate description."
