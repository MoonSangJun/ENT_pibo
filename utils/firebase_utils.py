from datetime import datetime
from firebase_config import db

def update_workout_score(user_id, workout_type, score, reps=12, sets=1, date=None):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    workout_ref = db.collection("users").document(user_id).collection(workout_type).document(date)
    workout_doc = workout_ref.get()

    prev_data = workout_doc.to_dict() if workout_doc.exists else {}
    prev_reps = prev_data.get("reps", 0)
    prev_sets = prev_data.get("sets", 0)
    prev_exp = prev_data.get("exp", 0)

    workout_ref.set({
        "reps": prev_reps + reps,
        "sets": prev_sets + sets,
        "exp": prev_exp + score
    }, merge=True)

    info_ref = db.collection("users").document(user_id)
    user_doc = info_ref.get()
    current_exp = user_doc.to_dict().get("exp", 0) if user_doc.exists else 0
    new_exp = current_exp + score

    level = 1
    threshold = 1000
    while new_exp >= threshold:
        level += 1
        threshold *= 2

    info_ref.set({
        "exp": new_exp,
        "level": level
    }, merge=True)