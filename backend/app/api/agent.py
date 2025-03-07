import os
from . import *
import traceback

from flask import current_app as app
from flask_restful import Resource, reqparse

from dotenv import load_dotenv

from backend.app.api.agent_tools import *
from backend.app.utils.strings import system_text44

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_firestore import FirestoreChatMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain.agents import tool, create_react_agent, AgentExecutor
from langchain import hub
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


# Loading environment variables
load_dotenv()

# Vector DB setup
current_dir = os.path.dirname(os.path.abspath(__file__))
persistent_directory = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "vector_database"))

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")
vector_db = Chroma(persist_directory=persistent_directory, embedding_function=embeddings)

llm_general = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Defining Syllabus Search Tool
@tool
def search_syllabus(query):
    """Using the user's input, searches the syllabus vector database for relevant content."""
    retriever = vector_db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 3, "score_threshold": 0.7},
    )
    relevant_chunks = retriever.invoke(query)
    
    if not relevant_chunks:
        return "The query is not relevant to the syllabus."
    
    return "\n\n".join([chunk.page_content for chunk in relevant_chunks])  # Converts list to string (easier for the AI Agent to use)

# Defining Tools
tools = [search_syllabus, get_chat_history]

custom_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_text44),
    HumanMessagePromptTemplate.from_template("User ID: {user_id}, Question: {input}")
])


# Creating Agent
agent = create_react_agent(llm_general, tools, custom_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

class MainAgent(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("user_id", type=int, required=True, help="The user is required")
            parser.add_argument("quest", type=str, required=True, help="A query is required")
            args = parser.parse_args()
            quest = args["quest"].strip()
            user_id = args["user_id"]

            if not quest:
                return {"Error": "A query is required"}, 400
            
            chat_history = FirestoreChatMessageHistory(
            session_id=str(user_id), collection=COLLECTION_NAME, client=client
            )
            
            chat_history.add_user_message(quest)

            response = agent_executor.invoke({"input": quest, "user_id": user_id})

            if isinstance(response, dict) and "output" in response:
                response_text = response["output"]  # Extracting response text if it's inside a dict
            else:
                response_text = str(response)  # Converting to string as a fallback

            chat_history.add_ai_message(response_text)  # Saving as a proper string

            return {"query": quest, "response": response_text}, 200

        except Exception as e:
            app.logger.error(f"Exception occurred: {e}")
            app.logger.error(traceback.format_exc())
            return {"Error": "Failed to process request"}, 500


api.add_resource(MainAgent, "/main_agent")

