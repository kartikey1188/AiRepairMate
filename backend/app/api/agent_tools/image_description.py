from langchain_google_genai import ChatGoogleGenerativeAI # LangChain wrapper for Google's Gemini chat models.
import google.generativeai as genai # Official Python SDK for Google's Gemini API (direct).
import base64 # For decoding image strings sent in base64 (likely via API or frontend).
import pytesseract # Python binding for Tesseract OCR — used to extract text from images.
from PIL import Image # Python Imaging Library — used to open and manipulate images
import io # Needed to convert bytes into something PIL can understand
import re # For regex-based cleanup
import os
from dotenv import load_dotenv # To securely load GOOGLE_API_KEY from .env

# Load env vars
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def clean_text(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()

def extract_text_from_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    extracted_text = pytesseract.image_to_string(image)
    return clean_text(extracted_text)

def is_meaningful_text(text: str) -> bool:
    return bool(text.strip()) 

def describe_with_google_sdk(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes))
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content([
        "Describe this image. What appliance is it, what model, and what issue might it have? Be specific and technical.",
        image
    ])
    return clean_text(response.text) if response and hasattr(response, "text") else "Could not generate visual description."

def describe_image(image: str):
    image_bytes = base64.b64decode(image)
    ocr_text = extract_text_from_image(image_bytes)

    if is_meaningful_text(ocr_text):
        model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.2,
            top_k=40,
            top_p=0.7,
            max_output_tokens=500
        )

        examples = [
            {
                "ocr": "HP Pavilion dv6000\nOperating System not found",
                "desc": "This is an HP Pavilion dv6000 laptop. The screen shows a BIOS error message: 'Operating System not found', which usually indicates a missing bootloader or a failed hard disk."
            },
            {
                "ocr": "LG Washing Machine Model WM3488HW\nError Code: OE",
                "desc": "This appears to be an LG WM3488HW washing machine. The OE error code points to a drainage issue, likely due to a clogged drain filter or blocked hose."
            },
            {
                "ocr": "Canon PIXMA MG2522\nPaper Jam\nError E03",
                "desc": "This is a Canon PIXMA MG2522 printer. It shows Error E03 and a 'Paper Jam' message, which means paper is likely stuck inside the feed mechanism or rollers."
            }
        ]

        messages = []
        for ex in examples:
            messages.append({"role": "user", "content": f"OCR Text:\n{ex['ocr']}"})
            messages.append({"role": "assistant", "content": ex["desc"]})

        # Run Gemini Vision
        visual_description = describe_with_google_sdk(image_bytes)

        # Add the combined prompt
        messages.append({
            "role": "user",
            "content": f"OCR Text:\n{ocr_text}\n\nVisual Description:\n{visual_description}\n\nUsing both the OCR and visual info, describe the appliance, its model (if possible), and the issue. Be specific and technical. If uncertain, make an educated guess and explain."
        })

        response = model.invoke(messages)
        return clean_text(response.content) if response else "Could not generate description."

    else:
        return describe_with_google_sdk(image_bytes)
