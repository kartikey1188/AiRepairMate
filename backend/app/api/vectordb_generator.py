import os
import traceback
import json
import re
import time 

from . import *
from flask import current_app as app
from flask_restful import Resource
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFaceHub

# Load environment variables
load_dotenv()

# Configurations
current_dir = os.path.dirname(os.path.abspath(__file__))
json_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "clean_data"))
persistent_directory = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "vector_database"))

# Initialize embeddings & vector database
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")

# Initialize Gemini model
llm_general = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

#llm_general = HuggingFaceHub(repo_id="meta-llama/Llama-3-8B-Instruct")


def clean_text(text):
    """Cleans LLM-generated text while preserving actual content."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Remove bold (**bold** → bold)
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # Remove italics (*italics* → italics)
    text = re.sub(r"_(.*?)_", r"\1", text)  # Remove underlines (_underline_ → underline)
    text = re.sub(r"`(.*?)`", r"\1", text)  # Remove inline code (`code` → code)
    text = re.sub(r"<.*?>", "", text)  # Remove HTML tags (if any)
    return text.strip()

def extract_title(data):
    """Extracts title from JSON data with fallback logic."""
    title = ""
    
    # Check metadata section first
    if "metadata" in data:
        metadata = data["metadata"]
        if "title" in metadata:
            title = metadata["title"]
        elif "guide_title" in metadata:
            title = metadata["guide_title"]
    
    # Fallback to root level title
    if not title and "title" in data:
        title = data["title"]
    
    return title.strip() if title else ""


def generate_gemini_summary(text, delay=2):
    """Generate structured context using Gemini 2.0 Flash with infinite retries and attempt logging."""
    attempt = 1  # Track attempt count

    while True:  # Keep retrying indefinitely
        try:
            response = llm_general.invoke(
                "Generate a concise repair guide summary. Include: "
                "- Appliance type\n"
                "- Model names\n"
                "- Repair title\n"
                "- Key steps\n"
                "- Critical components\n\n"
                f"Guide content:\n{text}"
            )
            if response and response.content:
                app.logger.info(f"Success on attempt {attempt}")
                return clean_text(response.content)
            
            app.logger.warning(f"Attempt {attempt}: Empty response received, retrying...")
        except Exception as e:
            app.logger.error(f"Gemini API Error (Attempt {attempt}): {e}")

        attempt += 1  # Increment attempt counter
        time.sleep(delay)  # Wait before retrying


class GenerateVectorDB(Resource):
    def get(self):
        try:
            app.logger.info("Starting vector DB generation process")
            if not os.path.exists(json_dir):
                app.logger.error(f"JSON directory {json_dir} not found")
                raise FileNotFoundError(f"JSON directory {json_dir} not found")

            json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]
            app.logger.info(f"Found {len(json_files)} JSON files in directory {json_dir}")
            documents = []
            count = 0

            for file in json_files:
                file_path = os.path.join(json_dir, file)
                app.logger.info(f"Processing file: {file_path}")
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    app.logger.info(f"Successfully loaded JSON file: {file_path}")
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    app.logger.error(f"Skipping invalid JSON file: {file} due to error: {e}")
                    continue

                # Extract filename and title
                filename = os.path.basename(file_path)
                title = extract_title(data)
                app.logger.info(f"Extracted title: '{title}' from file: {filename}")
                
                # Generate summary
                json_text = json.dumps(data, indent=2)
                summary = generate_gemini_summary(json_text)
                app.logger.info(f"Generated summary for file: {filename}")
                
                # Create document with metadata
                metadata = {"filename": filename, "title": title}
                documents.append((summary, metadata))
                count += 1

            app.logger.info(f"Processed {count} JSON files with {len(documents)} valid entries")

            if not documents:
                app.logger.warning("No valid documents found for vectorization")
                return {"error": "No valid documents found for vectorization"}, 400

            # Split into texts and metadata
            texts = [doc[0] for doc in documents]
            metadatas = [doc[1] for doc in documents]

            # Create and persist vector store
            Chroma.from_texts(
                texts=texts,
                embedding=embeddings,
                metadatas=metadatas,
                persist_directory=persistent_directory
            )
            app.logger.info(f"Vector DB created successfully with {len(texts)} entries at {persistent_directory}")
            return {
                "message": f"Vector DB created successfully with {len(texts)} entries",
                "persist_dir": persistent_directory,
                "files_added": len(texts)
            }, 200

        except Exception as e:
            app.logger.error(f"Vector DB creation failed: {str(e)}")
            app.logger.error(traceback.format_exc())
            return {"error": "Vector DB creation failed - check server logs"}, 500

api.add_resource(GenerateVectorDB, "/generate_vectordb")