import os
import traceback
import base64
from flask import request, jsonify, current_app as app
from flask_restful import Resource
from dotenv import load_dotenv
from . import *

from backend.app.api.agent_tools import *
from backend.app.utils.strings import system_text44
from backend.app.utils.finalizer import extract_final_data

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_google_firestore import FirestoreChatMessageHistory
from google.cloud import firestore

# Load environment variables
load_dotenv()

# Firestore setup
COLLECTION_NAME = "ai_repair_chat_history"
client = firestore.Client()

# Vector DB setup
current_dir = os.path.dirname(os.path.abspath(__file__))
persistent_directory = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "vector_database"))

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")
vector_db = Chroma(persist_directory=persistent_directory, embedding_function=embeddings)

llm_general = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Define tools
tools = [describe_audio, find_closest_match, describe_image, get_chat_history]

custom_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_text44),
    HumanMessagePromptTemplate.from_template(
        "User ID: {user_id}, Query: {input}, Image_Description: {image_description}, Audio_Description: {audio_description}"
    ),
])

# Create Agent
agent = create_react_agent(llm_general, tools, custom_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)


def convert_to_bytes(file):
    """Converts uploaded file to bytes."""
    return base64.b64encode(file.read()).decode("utf-8")


class MainAgent(Resource):
    def post(self):
        try:
            user_id = request.form.get("user_id", "Unknown User")
            query = request.form.get("query", "")
            image_file = request.files.get("image")
            audio_file = request.files.get("audio")

            image_bytes = convert_to_bytes(image_file) if image_file else None
            audio_bytes = convert_to_bytes(audio_file) if audio_file else None

            # Firestore chat history setup
            chat_history = FirestoreChatMessageHistory(
                session_id=str(user_id), collection=COLLECTION_NAME, client=client
            )
            
            if query:
                chat_history.add_user_message(query)
            
            # Prepare agent input
            agent_input = {
                "user_id": user_id,
                "input": query if query else "No Query Provided",
                "image_description": image_bytes if image_bytes else "No Image Provided",
                "audio_description": audio_bytes if audio_bytes else "No Audio Provided",
            }

            # Call agent
            agent_response = agent_executor.invoke(agent_input)
            
            # If response is metadata, process it; otherwise, return as-is
            if isinstance(agent_response, dict) and "filename" in agent_response:
                final_response = extract_final_data(agent_response)
            else:
                final_response = clean_text(agent_response) if agent_response else "No response from AI."

            chat_history.add_ai_message(final_response)

            return jsonify({"response": final_response}), 200

        except Exception as e:
            app.logger.error(f"Exception occurred: {e}")
            app.logger.error(traceback.format_exc())
            return jsonify({"Error": "Failed to process request"}), 500


api.add_resource(MainAgent, "/main_agent")
