import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Firebase 초기화 (이미 초기화되어 있으면 건너뜀)
if not firebase_admin._apps:
    cred = credentials.Certificate("ent-pibo-firebase-adminsdk-fbsvc-07ff86926b.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def check_daily_quest(user_id):
    today = datetime.today().strftime('%Y-%m-%d')
    exercises = ["bench", "squat", "deadlift"]
    total_sets = 0

    # 오늘 날짜 기준 운동 세트 수 합산
    for exercise in exercises:
        doc_ref = db.collection("users").document(user_id).collection(exercise).document(today)
        doc = doc_ref.get()
        if doc.exists:
            sets = doc.to_dict().get("sets", 0)
            total_sets += sets

    # 일일 퀘스트 완료 여부 확인
    quest_ref = db.collection("users").document(user_id).collection("daily_quest").document(today)
    if quest_ref.get().exists:
        print("✅ 오늘의 퀘스트는 이미 완료되었습니다.")
        return

    if total_sets >= 3:
        # 점수 추가
        exp_ref = db.collection("users").document(user_id).collection("total").document("exp")
        exp_doc = exp_ref.get()

        if exp_doc.exists:
            current_score = exp_doc.to_dict().get("score", 0)
            exp_ref.update({"score": current_score + 1000})
        else:
            exp_ref.set({"score": 1000})

        # 퀘스트 완료 기록
        quest_ref.set({"completed": True})
        print("🎉 일일 퀘스트 완료! 1000점이 추가되었습니다.")
    else:
        print(f"현재까지 세트 수: {total_sets}/3 — 아직 퀘스트 조건을 만족하지 않았습니다.")
