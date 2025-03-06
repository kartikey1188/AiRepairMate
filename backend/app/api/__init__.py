from flask_restful import Api
import firebase_admin
from firebase_admin import credentials, firestore

api = Api()

if not firebase_admin._apps:
    cred = credentials.Certificate("app/utils/service-account.json")
    firebase_admin.initialize_app(cred)


client = firestore.client()

from . import agent, vectordb_generator