# firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore

# 이미 초기화했는지 확인
if not firebase_admin._apps:
    cred = credentials.Certificate("/Users/moonsangjun/Desktop/캡스톤1/ENT_pibo 복사본/ent-pibo-firebase-adminsdk-fbsvc-c45280ac53.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
