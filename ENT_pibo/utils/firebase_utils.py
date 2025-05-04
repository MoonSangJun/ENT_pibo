from datetime import datetime, timedelta
from firebase_config import db
from google.cloud.firestore_v1.base_query import FieldFilter, BaseCompositeFilter

def update_workout_score(user_id, workout_type, score, reps, start_time, end_time, date=None):
    if date is None:
        date = start_time.strftime("%Y-%m-%d")

    duration = int((end_time - start_time).total_seconds())

    user_doc = db.collection("users").document(user_id).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
    else:
        user_data = {}

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
    workout_doc = workout_ref.get()
    prev_data = workout_doc.to_dict() if workout_doc.exists else {}

    updated_data = {
        "reps": prev_data.get("reps", 0) + reps,
        "exp": prev_data.get("exp", 0) + score,
        set_field: prev_data.get(set_field, 0) + set_count,
        "time": prev_data.get("time", 0) + duration,
        "date": date
    }
    workout_ref.set(updated_data, merge=True)

    info_ref = db.collection("users").document(user_id)
    current_exp = user_data.get("exp", 0)
    new_exp = current_exp + score

    level = 1
    exp_thresholds = [
        (10, 12000),
        (100, 84000),
        (1000, 360000),
        (float('inf'), 4380000)
    ]
    remaining_exp = new_exp
    for max_level, threshold in exp_thresholds:
        while level <= max_level and remaining_exp >= threshold:
            remaining_exp -= threshold
            level += 1

    info_ref.set({
        "exp": new_exp,
        "level": level,
    }, merge=True)

    recalculate_statistics(user_id, date)
    
    # 그룹 통계 업데이트
    group1 = user_data.get("group1")
    group2 = user_data.get("group2")

    if group1:
        recalculate_group_statistics(group1, date)
    if group2:
        recalculate_group_statistics(group2, date)

def recalculate_statistics(user_id, date_str):

    base_date = datetime.strptime(date_str, "%Y-%m-%d")

    # 기간별 시작일 계산
    periods = {
        "total": None,
        "daily": base_date,
        "weekly": base_date - timedelta(days=base_date.weekday()),
        "monthly": base_date.replace(day=1),
        "yearly": base_date.replace(month=1, day=1),
    }

    workout_types = ["bench", "deadlift", "squat"]

    for period_name, start_date in periods.items():
        # total은 모든 날짜 포함
        if period_name == "total":
            filters = []
        else:
            filters = [
                FieldFilter("date", ">=", start_date.strftime("%Y-%m-%d")),
                FieldFilter("date", "<=", date_str)
            ]

        b_reps = b_time = d_reps = d_time = s_reps = s_time = 0

        for workout_type in workout_types:
            query = db.collection("users").document(user_id).collection(workout_type)

            if filters:
                query = query.where(filter=BaseCompositeFilter('AND', filters))

            docs = query.stream()

            for doc in docs:
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

        stats_ref = db.collection("users").document(user_id).collection("statistics").document(period_name)
        stats_ref.set({
            "t_reps": t_reps,
            "t_time": t_time,
            "b_reps": b_reps,
            "b_time": b_time,
            "d_reps": d_reps,
            "d_time": d_time,
            "s_reps": s_reps,
            "s_time": s_time,
        }, merge=True)

    print(f"All statistics for user {user_id} have been recalculated.")

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
    user_ref = db.collection("users").document(user_id)
    user_data = user_ref.get().to_dict()
    return user_data.get("difficulty", "normal")

def listen_to_exercise(user_id, exercise_type):
    col_ref = db.collection("users").document(user_id).collection(exercise_type)

    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            doc = change.document
            recalculate_statistics(user_id, doc.id)

    col_ref.on_snapshot(on_snapshot)

def recalculate_group_statistics(group_id, date_str):


    base_date = datetime.strptime(date_str, "%Y-%m-%d")

    # 기간별 시작일 계산
    periods = {
        "total": None,
        "daily": base_date,
        "weekly": base_date - timedelta(days=base_date.weekday()),
        "monthly": base_date.replace(day=1),
        "yearly": base_date.replace(month=1, day=1),
    }

    workout_types = ["bench", "deadlift", "squat"]

    users_ref = db.collection("users")
    user_docs = users_ref.stream()

    group_users = []
    for user_doc in user_docs:
        data = user_doc.to_dict()
        if data:
            if data.get("group1") == group_id or data.get("group2") == group_id:
                group_users.append(user_doc.id)

    for period_name, start_date in periods.items():
        b_reps = b_time = d_reps = d_time = s_reps = s_time = total_exp = 0

        for user_id in group_users:
            # 1. 경험치 합산 (users/{uid}/statistics/{period_name} 문서의 exp 필드)
            stat_ref = db.collection("users").document(user_id).collection("statistics").document(period_name)
            stat_doc = stat_ref.get()
            if stat_doc.exists:
                exp = stat_doc.to_dict().get("exp", 0)
                total_exp += exp

            # 2. 운동 데이터 합산
            for workout_type in workout_types:
                query = db.collection("users").document(user_id).collection(workout_type)

                if period_name != "total":
                    filters = [
                        FieldFilter("date", ">=", start_date.strftime("%Y-%m-%d")),
                        FieldFilter("date", "<=", date_str)
                    ]
                    query = query.where(filter=BaseCompositeFilter('AND', filters))

                docs = query.stream()
                for doc in docs:
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
        if not group_ref.get().exists:
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
            })

        stats_ref = group_ref.collection("statistics").document(period_name)
        stats_ref.set({
            "t_reps": t_reps,
            "t_time": t_time,
            "b_reps": b_reps,
            "b_time": b_time,
            "d_reps": d_reps,
            "d_time": d_time,
            "s_reps": s_reps,
            "s_time": s_time
        }, merge=True)

    print(f"[GROUP {group_id}] Group statistics updated for all periods.")
