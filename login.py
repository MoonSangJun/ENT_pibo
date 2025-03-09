import firebase_admin
from firebase_admin import credentials, auth, firestore

cred = credentials.Certificate("/Users/moonsangjun/Desktop/캡스톤1/ENT_pibo/ent-pibo-firebase-adminsdk-fbsvc-07ff86926b.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def sign_up(email, password, name):
    user = auth.create_user(email=email, password=password)
    user_id = user.uid
    db.collection("users").document(user_id).set({
        "name": name, "email": email, "total_score": 0
    })
    return user_id

def login(email, password):
    try:
        user = auth.get_user_by_email(email)
        return user.uid
    except:
        return None
