# features/motivation/quests/dailyquest.py

from firebase_admin import firestore
from datetime import datetime

db = firestore.client()

# 로그인 시 퀘스트 문서 만들기
def create_daily_quest(user_id):
    today = datetime.now().strftime("%Y-%m-%d")

    # 사용자 문서 참조
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        print("사용자 문서를 찾을 수 없습니다.")
        return

    user_data = user_doc.to_dict()
    level = user_data.get("level", 1)

    # 오늘 날짜 기준 퀘스트 문서 확인 또는 생성
    quest_ref = user_ref.collection("quest").document(today)
    quest_doc = quest_ref.get()

    if quest_doc.exists:
        print("오늘의 퀘스트 문서가 이미 존재합니다. 업데이트를 생략합니다.")
        return  # 이미 존재하면 중복 생성 방지

    # 운동 기록 가져오기
    from utils.firebase_utils import get_today_stats
    stats = get_today_stats(user_id, today)
    total_reps = stats.get("b_reps", 0) + stats.get("d_reps", 0) + stats.get("s_reps", 0)
    total_time = stats.get("b_time", 0) + stats.get("d_time", 0) + stats.get("s_time", 0)

    # 퀘스트 문서 생성 (초기값 설정)
    quest_ref.set({
        "is_completed": False,
        "reward_exp": 0,
        "total_reps": total_reps,
        "total_time": total_time,
        "level": level,
        "date": today
    })

    print("퀘스트 문서 생성 완료.")

# 운동 후 퀘스트 조건 확인 및 점수 부여
def evaluate_daily_quest(user_id):
    from utils.firebase_utils import update_user_exp, recalculate_group_statistics
    today = datetime.now().strftime("%Y-%m-%d")

    # 사용자 문서 참조
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        print("사용자 문서를 찾을 수 없습니다.")
        return

    user_data = user_doc.to_dict()
    level = user_data.get("level", 1)

    # 오늘 날짜 기준 퀘스트 문서 확인
    quest_ref = user_ref.collection("quest").document(today)
    quest_doc = quest_ref.get()

    if not quest_doc.exists:
        print("오늘의 퀘스트 문서가 존재하지 않습니다. 문서를 생성해 주세요.")
        return

    # 운동 기록 가져오기
    from utils.firebase_utils import get_today_stats
    stats = get_today_stats(user_id, today)
    total_reps = stats.get("b_reps", 0) + stats.get("d_reps", 0) + stats.get("s_reps", 0)
    total_time = stats.get("b_time", 0) + stats.get("d_time", 0) + stats.get("s_time", 0)

    # 레벨 구간별 퀘스트 조건
    if 1 <= level <= 10:
        required_reps, required_time, reward_exp = 40, 2400, 1000
    elif 11 <= level <= 100:
        required_reps, required_time, reward_exp = 80, 3000, 3000
    elif 101 <= level <= 1000:
        required_reps, required_time, reward_exp = 120, 3600, 5000
    else:
        required_reps, required_time, reward_exp = 200, 4800, 10000

    # 조건 충족 여부
    is_completed = total_reps >= required_reps or total_time >= required_time
    final_exp = reward_exp if is_completed else 0

    # 퀘스트 결과 저장
    quest_ref.set({
        "is_completed": is_completed,
        "reward_exp": final_exp,
        "total_reps": total_reps,
        "total_time": total_time,
        "level": level,
        "date": today
    })

    print(f"퀘스트 평가 완료: {'성공' if is_completed else '실패'}, 경험치 저장: +{final_exp}")

    # 경험치 지급 (한 번만)
    if is_completed:
        update_user_exp(user_id, final_exp)
        # 그룹 통계 업데이트
        for group_id in [user_data.get("group1"), user_data.get("group2")]:
            if group_id:
                recalculate_group_statistics(group_id, today)
