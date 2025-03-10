import os
import traceback
import base64
import ast
from flask import request, jsonify, current_app as app
from flask_restful import Resource
from dotenv import load_dotenv
from . import *
import google.generativeai as genai

from backend.app.api.agent_tools import *
from backend.app.utils.strings import *
from backend.app.utils.finalizer import extract_final_data

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_google_firestore import FirestoreChatMessageHistory
from google.cloud import firestore

# Loading environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Firestore setup
COLLECTION_NAME = "ai_repair_chat_history"
client = firestore.Client()

# Vector DB setup
current_dir = os.path.dirname(os.path.abspath(__file__))
persistent_directory = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "vector_database"))

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")
vector_db = Chroma(persist_directory=persistent_directory, embedding_function=embeddings)

llm_general = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Defining tools
tools = [find_closest_match, get_chat_history]

custom_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_text44),
    HumanMessagePromptTemplate.from_template(
        "User ID: {user_id}, Query: {input}, Image Description: {image}, Audio Description: {audio}"
    )
])

# Creating Agent
agent = create_react_agent(llm_general, tools, custom_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)


def convert_to_base64(file):
    """Converts uploaded file to a base64 string."""
    return base64.b64encode(file.read()).decode("utf-8") if file else None

def google_ai_python_sdk_for_gemini_api(input):
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(
        f"""From the following code, give me every step and any sort of title and description related to that step, and any image links related to that step too. Also, give me the embed code, and the tools required as well.

        {input}
        """
    )
    return clean_text(response.text) if response and hasattr(response, "text") else "Could not generate description."

class MainAgent(Resource):
    def post(self):
        try:
            user_id = request.form.get("user_id", "Unknown User")
            query = request.form.get("query", "")
            image_file = request.files.get("image")
            audio_file = request.files.get("audio")

            image_description = "No Image Provided"
            audio_description = "No Audio Provided"

            if image_file:
                image_bytes = convert_to_base64(image_file)
                image_description = describe_image(image_bytes) if image_bytes else "Couldn't convert to base64 successfully."
            
            print("Image description:", image_description)

            if audio_file:
                audio_bytes = convert_to_base64(audio_file)
                audio_description = describe_audio(audio_bytes) if audio_bytes else "Couldn't convert to base64 successfully."
            
            print("Audio description:", audio_description)

            # Firestore chat history setup
            chat_history = FirestoreChatMessageHistory(
                session_id=str(user_id), collection=COLLECTION_NAME, client=client
            )
            
            if query:
                chat_history.add_user_message(query)
            
            # Preparing agent input
            agent_input = {
                "user_id": user_id,
                "input": query if query else "No Query Provided",
                "image": image_description,
                "audio": audio_description
            }

            # Calling agent
            agent_response = agent_executor.invoke(agent_input)

            # Extracting text response from the agent's output dictionary
            output_text = agent_response.get("output", "")  # Get text or empty string

            print("Output_text:", output_text)

            try:
                check_dict = ast.literal_eval(output_text)
            except (ValueError, SyntaxError):
                check_dict = output_text  

            if isinstance(check_dict, dict) and "filename" in check_dict:
                final_response = google_ai_python_sdk_for_gemini_api(extract_final_data(check_dict))
            else:
                final_response = clean_text(output_text) if output_text else "No response from AI."

            chat_history.add_ai_message(str(final_response))

            if not isinstance(final_response, (dict, str, list)):
                final_response = str(final_response)  

            return {"response": final_response}, 200

        except Exception as e:
            app.logger.error(f"Exception occurred: {e}")
            app.logger.error(traceback.format_exc())
            return {"Error": "Failed to process request"}, 500


api.add_resource(MainAgent, "/main_agent")
