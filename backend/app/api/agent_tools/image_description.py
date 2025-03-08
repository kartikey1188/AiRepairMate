from backend.app.api import *
from langchain.agents import tool
from langchain_google_genai import ChatGoogleGenerativeAI
import base64
import re
import pytesseract
from PIL import Image
import io

MODEL_NAME = "gemini-2.0-flash"

def clean_text(text):
    """Cleans LLM-generated text while preserving actual content."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Remove bold (**bold** → bold)
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # Remove italics (*italics* → italics)
    text = re.sub(r"_(.*?)_", r"\1", text)  # Remove underlines (_underline_ → underline)
    text = re.sub(r"`(.*?)`", r"\1", text)  # Remove inline code (`code` → code)
    text = re.sub(r"<.*?>", "", text)  # Remove HTML tags (if any)
    return text.strip()

def extract_text_from_image(image_bytes):
    """Extracts text from an image using OCR (Tesseract)."""
    image = Image.open(io.BytesIO(image_bytes))
    extracted_text = pytesseract.image_to_string(image)
    return clean_text(extracted_text)  # Apply cleaning to OCR result

def describe_image(image: str):
    """Takes an image as input, extracts text using OCR, then generates a detailed description using Gemini-2.0-Flash-Exp-Image. Focus on finding and describing what the particular appliance/thing is, what its exact model is, and what the issue is."""
    
    image_bytes = base64.b64decode(image)

    # Step 1: Extract and clean text using OCR
    ocr_text = extract_text_from_image(image_bytes)
    
    # Step 2: Get contextual description from Gemini
    model = ChatGoogleGenerativeAI(model=MODEL_NAME)
    
    response = model.invoke([
        {"role": "system", "content": "Describe the image in detail, including objects, scene, and any visible text."},
        {"role": "user", "content": f"Here is an image. Analyze it and describe the objects, scene, and text found in it."},
        {"role": "user", "content": image}  # Properly passing base64 image
    ])
    
    gemini_description = clean_text(response.content) if response else "Could not generate description."
    
    # Step 3: Combine both responses
    final_description = f"OCR Extracted Text: {ocr_text}\n\nGemini Description: {gemini_description}"
    
    return final_description
