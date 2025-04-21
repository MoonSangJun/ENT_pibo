import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Firebase �ʱ�ȭ (�̹� �ʱ�ȭ�Ǿ� ������ �ǳʶ�)
if not firebase_admin._apps:
    cred = credentials.Certificate("ent-pibo-firebase-adminsdk-fbsvc-07ff86926b.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def check_daily_quest(user_id):
    today = datetime.today().strftime('%Y-%m-%d')
    exercises = ["bench", "squat", "deadlift"]
    total_sets = 0

    # ���� ��¥ ���� � ��Ʈ �� �ջ�
    for exercise in exercises:
        doc_ref = db.collection("users").document(user_id).collection(exercise).document(today)
        doc = doc_ref.get()
        if doc.exists:
            sets = doc.to_dict().get("sets", 0)
            total_sets += sets

    # ���� ����Ʈ �Ϸ� ���� Ȯ��
    quest_ref = db.collection("users").document(user_id).collection("daily_quest").document(today)
    if quest_ref.get().exists:
        print("? ������ ����Ʈ�� �̹� �Ϸ�Ǿ����ϴ�.")
        return

    if total_sets >= 3:
        # ���� �߰�
        exp_ref = db.collection("users").document(user_id).collection("total").document("exp")
        exp_doc = exp_ref.get()

        if exp_doc.exists:
            current_score = exp_doc.to_dict().get("score", 0)
            exp_ref.update({"score": current_score + 1000})
        else:
            exp_ref.set({"score": 1000})

        # ����Ʈ �Ϸ� ���
        quest_ref.set({"completed": True})
        print("? ���� ����Ʈ �Ϸ�! 1000���� �߰��Ǿ����ϴ�.")
    else:
        print(f"������� ��Ʈ ��: {total_sets}/3 ? ���� ����Ʈ ������ �������� �ʾҽ��ϴ�.")