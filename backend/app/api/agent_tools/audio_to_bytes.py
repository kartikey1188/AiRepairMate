# @app.route("/process-audio", methods=["POST"])
# def process_audio():
#     if "file" not in request.files:
#         return {"error": "No file uploaded"}, 400

#     audio = request.files["file"].read()  # Read audio as bytes
#     response = describe_audio(audio)  # Pass raw bytes to the agent
    
#     return {"transcription": response}