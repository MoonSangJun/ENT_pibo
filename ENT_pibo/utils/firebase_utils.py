from datetime import datetime, timedelta
from firebase_admin import firestore
from firebase_config import db
from features.motivation.quests.dailyquest import evaluate_daily_quest
from google.cloud.firestore_v1.base_query import FieldFilter, BaseCompositeFilter

def update_workout_score(user_id, workout_type, score, reps, start_time, end_time, date=None):
    if date is None:
        date = start_time.strftime("%Y-%m-%d")

    duration = int((end_time - start_time).total_seconds())

    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict() if user_doc.exists else {}

    difficulty = user_data.get("difficulty", "normal")
    if difficulty == "easy":
        set_count = reps // 8
        set_field = "easy_set"
    elif difficulty == "hard":
        set_count = reps // 15
        set_field = "hard_set"
    else:
        set_count = reps // 12
        set_field = "normal_set"

    workout_ref = db.collection("users").document(user_id).collection(workout_type).document(date)
    prev_data = workout_ref.get().to_dict() or {}

    updated_data = {
        "reps": prev_data.get("reps", 0) + reps,
        "exp": prev_data.get("exp", 0) + score,
        set_field: prev_data.get(set_field, 0) + set_count,
        "time": prev_data.get("time", 0) + duration,
        "date": date
    }
    workout_ref.set(updated_data, merge=True)

    new_exp = user_data.get("exp", 0) + score
    level = 1
    exp_thresholds = [(10, 12000), (100, 84000), (1000, 360000), (float('inf'), 4380000)]

    remaining_exp = new_exp
    for max_level, threshold in exp_thresholds:
        while level <= max_level and remaining_exp >= threshold:
            remaining_exp -= threshold
            level += 1

    db.collection("users").document(user_id).set({
        "exp": new_exp,
        "level": level,
    }, merge=True)

    recalculate_statistics(user_id, date)

    # 그룹 통계 업데이트
    for group_id in [user_data.get("group1"), user_data.get("group2")]:
        if group_id:
            recalculate_group_statistics(group_id, date)
            
    evaluate_daily_quest(user_id)

def recalculate_statistics(user_id, date_str):
    base_date = datetime.strptime(date_str, "%Y-%m-%d")
    periods = {
        "total": None,
        "daily": base_date,
        "weekly": base_date - timedelta(days=base_date.weekday()),
        "monthly": base_date.replace(day=1),
        "yearly": base_date.replace(month=1, day=1),
    }

    workout_types = ["bench", "deadlift", "squat"]

    for period_name, start_date in periods.items():
        filters = [] if period_name == "total" else [
            FieldFilter("date", ">=", start_date.strftime("%Y-%m-%d")),
            FieldFilter("date", "<=", date_str)
        ]

        b_reps = b_time = d_reps = d_time = s_reps = s_time = 0

        for workout_type in workout_types:
            query = db.collection("users").document(user_id).collection(workout_type)
            if filters:
                query = query.where(filter=BaseCompositeFilter('AND', filters))
            for doc in query.stream():
                data = doc.to_dict()
                reps = data.get("reps", 0)
                time = data.get("time", 0)
                if workout_type == "bench":
                    b_reps += reps
                    b_time += time
                elif workout_type == "deadlift":
                    d_reps += reps
                    d_time += time
                elif workout_type == "squat":
                    s_reps += reps
                    s_time += time

        t_reps = b_reps + d_reps + s_reps
        t_time = b_time + d_time + s_time

        db.collection("users").document(user_id).collection("statistics").document(period_name).set({
            "t_reps": t_reps, "t_time": t_time,
            "b_reps": b_reps, "b_time": b_time,
            "d_reps": d_reps, "d_time": d_time,
            "s_reps": s_reps, "s_time": s_time
        }, merge=False)

def recalculate_group_statistics(group_id, date_str):
    base_date = datetime.strptime(date_str, "%Y-%m-%d")
    periods = {
        "total": None,
        "daily": base_date,
        "weekly": base_date - timedelta(days=base_date.weekday()),
        "monthly": base_date.replace(day=1),
        "yearly": base_date.replace(month=1, day=1),
    }

    workout_types = ["bench", "deadlift", "squat"]

    user_docs = db.collection("users").stream()
    group_users = []
    total_exp = 0
    user_list = []

    for doc in user_docs:
        data = doc.to_dict()
        if data and (data.get("group1") == group_id or data.get("group2") == group_id):
            user_id = doc.id
            group_users.append(user_id)
            user_list.append({
                "email": data.get("email"),
                "user_id": user_id,
                "nickname": data.get("nickname"),
            })
            total_exp += data.get("exp", 0)

    for period_name, start_date in periods.items():
        b_reps = b_time = d_reps = d_time = s_reps = s_time = 0

        for user_id in group_users:
            for workout_type in workout_types:
                query = db.collection("users").document(user_id).collection(workout_type)
                if period_name != "total":
                    filters = [
                        FieldFilter("date", ">=", start_date.strftime("%Y-%m-%d")),
                        FieldFilter("date", "<=", date_str)
                    ]
                    query = query.where(filter=BaseCompositeFilter('AND', filters))
                for doc in query.stream():
                    data = doc.to_dict()
                    reps = data.get("reps", 0)
                    time = data.get("time", 0)
                    if workout_type == "bench":
                        b_reps += reps
                        b_time += time
                    elif workout_type == "deadlift":
                        d_reps += reps
                        d_time += time
                    elif workout_type == "squat":
                        s_reps += reps
                        s_time += time

        t_reps = b_reps + d_reps + s_reps
        t_time = b_time + d_time + s_time

        group_ref = db.collection("groups").document(group_id)
        group_ref.set({
            "group_name": group_id,
            "user_count": len(group_users),
            "exp": total_exp,
            "t_reps": t_reps,
            "t_time": t_time,
            "b_reps": b_reps,
            "b_time": b_time,
            "d_reps": d_reps,
            "d_time": d_time,
            "s_reps": s_reps,
            "s_time": s_time
        }, merge=True)

        group_ref.collection("statistics").document(period_name).set({
            "t_reps": t_reps,
            "t_time": t_time,
            "b_reps": b_reps,
            "b_time": b_time,
            "d_reps": d_reps,
            "d_time": d_time,
            "s_reps": s_reps,
            "s_time": s_time
        }, merge=True)

        group_ref.collection("statistics").document("user_list").set({
            "users": user_list
        }, merge=True)

def update_user_settings(user_id, nickname=None, pibo_mode=None, group1=None, group2=None, difficulty=None):
    update_data = {}
    if nickname:
        update_data['nickname'] = nickname
    if pibo_mode in ['soft', 'normal', 'hard']:
        update_data['pibo_mode'] = pibo_mode
    if group1:
        update_data['group1'] = group1
    if group2:
        update_data['group2'] = group2
    if difficulty in ['easy', 'normal', 'hard']:
        update_data['difficulty'] = difficulty

    if update_data:
        db.collection("users").document(user_id).set(update_data, merge=True)
        return True
    return False

def get_user_difficulty(user_id):
    user_doc = db.collection("users").document(user_id).get()
    if not user_doc.exists:
        return "normal"
    return user_doc.to_dict().get("difficulty", "normal")

def get_today_stats(user_id, date):
    stats_doc = db.collection("users").document(user_id).collection("statistics").document("daily").get()
    if not stats_doc.exists:
        return {"b_reps": 0, "d_reps": 0, "s_reps": 0, "b_time": 0, "d_time": 0, "s_time": 0}
    return stats_doc.to_dict()

def update_user_exp(user_id, exp_gain):
    db.collection("users").document(user_id).update({
        "exp": firestore.Increment(exp_gain)
    })

def listen_to_exercise(user_id, exercise_type):
    col_ref = db.collection("users").document(user_id).collection(exercise_type)
    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            doc = change.document
            recalculate_statistics(user_id, doc.id)
    col_ref.on_snapshot(on_snapshot)
    
def reset_daily_statistics_if_needed(user_id):
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. bench 기록 확인
    bench_ref = db.collection("users").document(user_id).collection("bench").document(today)
    bench_doc = bench_ref.get()

    # 2. squat 기록 확인
    squat_ref = db.collection("users").document(user_id).collection("squat").document(today)
    squat_doc = squat_ref.get()

    # 3. deadlift 기록 확인
    deadlift_ref = db.collection("users").document(user_id).collection("deadlift").document(today)
    deadlift_doc = deadlift_ref.get()

    # 4. 모든 운동이 없으면 초기화 진행
    if not bench_doc.exists and not squat_doc.exists and not deadlift_doc.exists:
        stats_ref = db.collection("users").document(user_id).collection("statistics").document("daily")
        stats_ref.set({
            "b_reps": 0,
            "b_time": 0,
            "d_reps": 0,
            "d_time": 0,
            "s_reps": 0,
            "s_time": 0,
            "t_reps": 0,
            "t_time": 0
        }, merge=True)  # merge=True: 다른 필드는 유지

def admin_update_all_users_and_groups():
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 🔁 1. 모든 사용자에 대해 통계 최신화
    user_docs = db.collection("users").stream()
    user_ids = []
    for doc in user_docs:
        user_id = doc.id
        user_ids.append(user_id)
        try:
            reset_daily_statistics_if_needed(user_id)
            recalculate_statistics(user_id, today_str)
        except Exception as e:
            print(f"❌ Failed to update user {user_id}: {e}")

    # 🔁 2. 모든 그룹 ID 수집
    group_ids = set()
    for user_id in user_ids:
        user_data = db.collection("users").document(user_id).get().to_dict()
        if user_data:
            if user_data.get("group1"):
                group_ids.add(user_data["group1"])
            if user_data.get("group2"):
                group_ids.add(user_data["group2"])

    # 🔁 3. 모든 그룹 통계 최신화
    for group_id in group_ids:
        try:
            recalculate_group_statistics(group_id, today_str)
        except Exception as e:
            print(f"❌ Failed to update group {group_id}: {e}")
