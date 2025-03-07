# from flask import Flask, request
# from backend.app.api import *  # Import your agent functions

# app = Flask(__name__)

# @app.route("/process-image", methods=["POST"])
# def process_image():
#     if "file" not in request.files:
#         return {"error": "No file uploaded"}, 400

#     image = request.files["file"].read()  # Read image as bytes
#     response = describe_image(image)  # Pass raw bytes to the agent
    
#     return {"description": response}

# if __name__ == "__main__":
#     app.run(debug=True)
