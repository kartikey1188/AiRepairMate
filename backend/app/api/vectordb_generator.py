import os
import traceback
import json
import re

from . import *

from flask import current_app as app
from flask_restful import Resource
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter


# Load environment variables
load_dotenv()

# Configurations
current_dir = os.path.dirname(os.path.abspath(__file__))
json_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "clean_data"))
persistent_directory = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "vector_database"))

# Initialize embeddings & vector database
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")

# Initialize Gemini model
llm_general = ChatGoogleGenerativeAI(model="gemini-2.0-flash")


def extract_url_metadata(data, parent_key=""):
    """Recursively extract all URLs from JSON and keep their associated keys."""
    url_metadata = {}

    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            url_metadata.update(extract_url_metadata(value, full_key))

    elif isinstance(data, list):
        for index, item in enumerate(data):
            full_key = f"{parent_key}[{index}]"
            url_metadata.update(extract_url_metadata(item, full_key))

    elif isinstance(data, str):
        urls = re.findall(r"https?://[^\s<>\"']+", data)
        if urls:
            url_metadata[parent_key] = urls  # Store URLs under their respective keys

    return url_metadata


def generate_gemini_summary(text):
    """Generate structured context using Gemini 2.0 Flash."""
    try:
        response = llm_general.invoke(f"Summarize this repair guide while preserving context:\n\n{text}")
        return response.content if response and response.content else "No summary available."
    except Exception as e:
        app.logger.error(f"Gemini API Error: {e}")
        return "Failed to generate summary."


class GenerateVectorDB(Resource):
    def get(self):
        try:
            if not os.path.exists(json_dir):
                raise FileNotFoundError(f"The directory {json_dir} does not exist.")

            vector_db = Chroma(persist_directory=persistent_directory, embedding_function=embeddings)
            
            json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]
            documents = []
            count = 0

            for file in json_files:
                file_path = os.path.join(json_dir, file)

                # Read JSON data
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        print(f"Skipping {file}: Invalid JSON format.")
                        continue

                # Extract URLs with their keys
                url_metadata = extract_url_metadata(data)
                if not url_metadata:
                    print(f"No URLs found in {file}, skipping.")
                    continue

                # Convert JSON to text & generate LLM summary
                json_text = json.dumps(data, indent=2)
                context_summary = generate_gemini_summary(json_text)

                # Create final chunk with URLs + LLM context
                final_text = f"Context: {context_summary}\n\nRelevant URLs:\n" + json.dumps(url_metadata, indent=2)
                metadata = {"source_file": file, "url_metadata": url_metadata}  # Store URLs as key-value pairs

                documents.append((final_text, metadata))
                count += 1

            print(f"Processed {count} JSON files.")

            # Split documents into chunks
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
            texts, metadatas = zip(*documents)
            chunks = text_splitter.split_text("\n".join(texts))

            if not chunks:
                print("No valid chunks to store! Exiting.")
                return {"Error": "No data to store in vector DB"}, 500

            print("\n--- Creating embeddings ---")
            embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")

            print("\n--- Creating and persisting vector store ---")
            vector_db = Chroma.from_texts(
                chunks, embeddings, metadatas=[{"source": "json_data"}] * len(chunks),
                persist_directory=persistent_directory
            )

            print("Vector database saved successfully.")

        except Exception as e:
            app.logger.error(f"Exception occurred: {e}")
            app.logger.error(traceback.format_exc())
            return {"Error": "Failed to create the vector database"}, 500


api.add_resource(GenerateVectorDB, "/generate_vectordb")