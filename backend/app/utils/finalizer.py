import json
import os

current_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current file
json_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "clean_data")) # Get the directory of the JSON files

def extract_final_data(metadata: dict):
    """Extracts relevant fields from the JSON file using the given metadata."""
    file_name = metadata.get("filename")
    if not file_name:
        return {"error": "Filename not provided in metadata"}
    
    file_path = os.path.join(json_dir, file_name) # Get the full path of the JSON file
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}
    except Exception as e:
        return {"error": f"Failed to read JSON file: {str(e)}"}
    
    response = {}
    
    # Extract 'title' from root or metadata
    title = data.get("title") or data.get("metadata", {}).get("title")
    if title:
        response["title"] = title
    
    # Extract 'tools' or 'tools_needed' from root
    tools = data.get("tools") or data.get("tools_needed") or data.get("tools_and_materials")
    if tools:
        response["tools"] = tools
    
    # Extract 'steps' from root
    steps = data.get("steps")
    if steps:
        response["steps"] = steps
    
    # Extract 'embed_code' from root
    embed_code = data.get("embed_code")
    if embed_code:
        response["embed_code"] = embed_code
    
    # Extract 'embed_guide' from root
    embed_guide = data.get("embed_guide")
    if embed_guide:
        response["embed_guide"] = embed_guide
    
    return response

