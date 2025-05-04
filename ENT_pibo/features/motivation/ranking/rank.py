from datetime import datetime, timedelta
from firebase_admin import firestore

db = firestore.client()

# 주기 키와 실제 날짜 키 매핑 함수
def get_period_key(period, date_str):
    if date_str is None:
        date_str = datetime.today().strftime("%Y-%m-%d")

    if period == "total":
        return "total"
    elif period == "daily":
        return date_str
    elif period == "weekly":
        start = datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=datetime.strptime(date_str, "%Y-%m-%d").weekday())
        return start.strftime("%Y-%m-%d")
    elif period == "monthly":
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m")
    elif period == "yearly":
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y")
    return None

# 유저의 주요 데이터 가져오기 (경험치, 운동시간, 운동횟수)
def get_user_field(user_id, field):
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    if user_doc.exists:
        return user_doc.to_dict().get(field)
    return None

# 운동별 경험치, 운동시간, 운동횟수 가져오기
def get_exercise_stat(user_id, period_key, exercise, field):
    stat_ref = db.collection("users").document(user_id).collection("statistics").document(period_key)
    stat_doc = stat_ref.get()
    if stat_doc.exists:
        return stat_doc.to_dict().get(exercise, {}).get(field)
    return None

# 경험치 비교 함수 (유저와 그룹)
def compare_exp(user_id, group_id=None):
    if group_id:
        group_ref = db.collection("groups").document(group_id)
        group_doc = group_ref.get()
        if not group_doc.exists:
            print("존재하지 않는 그룹입니다.")
            return
        group_exp = group_doc.to_dict().get("exp", 0)
        user_exp = get_user_field(user_id, "exp")
        if user_exp is not None:
            if user_exp > group_exp:
                print(f"{user_id}님의 경험치가 {group_id} 그룹보다 높습니다!")
            elif user_exp < group_exp:
                print(f"{user_id}님의 경험치가 {group_id} 그룹보다 낮습니다!")
            else:
                print(f"{user_id}님의 경험치와 {group_id} 그룹의 경험치가 같습니다.")
        else:
            print("유저의 경험치가 존재하지 않습니다.")
    else:
        user_exp = get_user_field(user_id, "exp")
        if user_exp is not None:
            print(f"{user_id}님의 경험치는 {user_exp}입니다.")
        else:
            print("유저의 경험치가 존재하지 않습니다.")

# 운동시간, 운동횟수 순위 비교
def compare_exercise_stat(user_id, group_id, exercise, field, period):
    period_key = get_period_key(period, None)
    user_scores = []

    if group_id:
        group_ref = db.collection("groups").document(group_id)
        group_doc = group_ref.get()
        if group_doc.exists:
            members = group_doc.to_dict().get("members", [])
            for member in members:
                stat_value = get_exercise_stat(member, period_key, exercise, field)
                if stat_value is not None:
                    user_scores.append((member, stat_value))

        sorted_scores = sorted(user_scores, key=lambda x: x[1], reverse=True)
        user_ranking = next((i + 1 for i, (uid, _) in enumerate(sorted_scores) if uid == user_id), None)
        print(f"{exercise} {field} - {user_id}님의 순위: {user_ranking}위 (전체 {len(sorted_scores)}명 중)")
    else:
        stat_value = get_exercise_stat(user_id, period_key, exercise, field)
        if stat_value is not None:
            print(f"{exercise} {field} - {user_id}님의 {field}: {stat_value}")
        else:
            print(f"{exercise} {field} 데이터가 존재하지 않습니다.")

# 개인 순위 출력
def print_individual_ranking(user_id):
    periods = ["total", "yearly", "monthly", "weekly", "daily"]
    exercises = ["deadlift", "squat", "bench"]
    criteria = ["운동시간", "운동횟수"]

    # 경험치 순위 확인
    compare_exp(user_id)

    for period in periods:
        print(f"\n[{period.upper()}]")
        for exercise in exercises:
            print(f"- {exercise.capitalize()}")
            for crit in criteria:
                compare_exercise_stat(user_id, None, exercise, crit, period)

# 그룹 순위 출력
def print_group_ranking(group_id, user_id):
    periods = ["total", "yearly", "monthly", "weekly", "daily"]
    exercises = ["deadlift", "squat", "bench"]
    criteria = ["운동시간", "운동횟수"]

    for period in periods:
        print(f"\n[{period.upper()}]")
        for exercise in exercises:
            print(f"- {exercise.capitalize()}")
            for crit in criteria:
                compare_exercise_stat(user_id, group_id, exercise, crit, period)

# 예시로 개인과 그룹 순위를 출력하는 함수 호출
user_id = "user123"  # 예시 유저 ID
group_id = "group1"  # 예시 그룹 ID

# 개인 순위 출력
print_individual_ranking(user_id)

# 그룹 순위 출력
print_group_ranking(group_id, user_id)
