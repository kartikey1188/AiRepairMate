from backend.app.api import *
import base64
import re
import os
import time
from dotenv import load_dotenv

from vertexai.generative_models import GenerativeModel, Part
import vertexai
from google.oauth2 import service_account

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")  # Set this in your .env
LOCATION = "us-central1"
SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_JSON")  

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH)
vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

def clean_text(text):
    """Cleans LLM-generated text while preserving actual content."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()

def describe_video(video: str):
    """Takes base64-encoded video (e.g. .mp4), uploads it via Vertex AI Part, and returns a detailed description."""

    video_bytes = base64.b64decode(video)

    # Write the decoded bytes to a temporary file
    temp_path = "temp_video.mp4"
    with open(temp_path, "wb") as f:
        f.write(video_bytes)

    model = GenerativeModel("gemini-1.5-pro")

    video_part = Part.from_data(data=video_bytes, mime_type="video/mp4")

    prompt = "Describe this video in detail. Include visual content, actions, objects, and transcribe the audio if present. Try to identify any appliances, devices, or repair scenarios shown."

    try:
        response = model.generate_content([video_part, prompt])
        return clean_text(response.text) if response and hasattr(response, "text") else "Could not generate description."
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
