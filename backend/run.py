import os
import sys
from flask import Flask, render_template
from flask_cors import CORS


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.api import api

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend', static_url_path='/static')

api.init_app(app)

CORS(app, supports_credentials=True)

@app.route('/', methods=['GET'])
def main_page():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)