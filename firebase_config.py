import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("/Users/cgi/ENT_pibo/ent-pibo-firebase-adminsdk-fbsvc-c45280ac53.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
