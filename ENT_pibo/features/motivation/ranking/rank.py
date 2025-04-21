from firebase_config import db

def print_user_ranking(top_n=10):
    print("? 사용자 랭킹 TOP", top_n)
    print("-" * 35)

    users_ref = db.collection("users")
    query = users_ref.order_by("exp", direction="DESCENDING").limit(top_n)
    results = query.stream()

    rank = 1
    for doc in results:
        user = doc.to_dict()
        name = user.get("name", "이름없음")
        exp = user.get("exp", 0)
        level = user.get("level", 1)

        print(f"{rank}위 | {name} | 레벨: {level} | 경험치: {exp}")
        rank += 1