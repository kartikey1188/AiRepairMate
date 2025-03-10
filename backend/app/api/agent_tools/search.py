from backend.app.api import *
from langchain.agents import tool
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

# Configurations
current_dir = os.path.dirname(os.path.abspath(__file__))
persistent_directory = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "data", "vector_database"))

# Initialize embeddings & vector database
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")
vector_db = Chroma(persist_directory=persistent_directory, embedding_function=embeddings)

@tool
def find_closest_match(query: str):
    """Finds the most relevant document in the vector database based on similarity search and returns its metadata."""
    results = vector_db.similarity_search_with_score(query, k=1)  # Get the top match

    # results will be a list of tuples, each containing a document and its similarity score

    if not results:
        return {"error": "No matches found in the vector database."}
    
    doc, score = results[0]  # Extract top match - the first tuple in the list
    
    # Enforce score threshold
    score_threshold = 0.6
    if score > score_threshold:
        return "No match passed the similarity score threshold."
    
    metadata = doc.metadata
    metadata["similarity_score"] = score  # Include similarity score in output

    return metadata
