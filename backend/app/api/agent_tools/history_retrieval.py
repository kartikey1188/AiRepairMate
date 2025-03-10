from backend.app.api import *
from langchain.agents import tool
from langchain_google_firestore import FirestoreChatMessageHistory

COLLECTION_NAME = "ai_repair_chat_history"

@tool
def get_chat_history(user_id):
    """Retrieves the chat history for the given user from Firestore Database."""
    chat_history = FirestoreChatMessageHistory(
        session_id=str(user_id), collection=COLLECTION_NAME, client=client
    )
    if not chat_history.messages:
        return "No chat history found."
    
    last_5_messages = chat_history.messages[-5:]

    return last_5_messages