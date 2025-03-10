import os
import sys
from flask import Flask, render_template
from flask_cors import CORS


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.api import api

app = Flask(__name__)

api.init_app(app)

CORS(app, supports_credentials=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)