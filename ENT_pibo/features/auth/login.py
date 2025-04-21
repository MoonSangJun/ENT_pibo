import firebase_admin
from firebase_admin import credentials, auth, firestore
from firebase_config import db


#회원가입 함수
def sign_up():
    name = input("이름을 입력하세요: ")
    password = input("비밀번호를 입력하세요 (6자리 숫자): ")

    if len(password) != 6 or not password.isdigit():
        print("비밀번호는 6자리 숫자여야 합니다.")
        return None

    email = f"{name}@example.com"  # 이메일 형식으로 변환 (Firebase 요구 사항)
    
    try:
        user = auth.create_user(email=email, password=password)
        user_id = user.uid

        # Firestore에 사용자 정보 저장
        db.collection("users").document(user_id).set({
            "name": name,
            "email": email,
            "total_score": 0  # 초기 점수
        })
        print(f"회원가입 성공! {name}님 환영합니다!")
        return user_id
    except Exception as e:
        print(f"회원가입 실패: {e}")
        return None

#로그인 함수
def login():
    name = input("이름을 입력하세요: ")
    password = input("비밀번호를 입력하세요: ")

    email = f"{name}@example.com"  # 저장된 이메일 형식과 일치시킴

    try:
        user = auth.get_user_by_email(email)
        print(f"로그인 성공! {name}님 환영합니다!")
        return user.uid
    except Exception:
        print("로그인 실패! 이름 또는 비밀번호가 올바르지 않습니다.")
        return None

# 실행
if __name__ == "__main__":
    while True:
        print("\nENT_Pibo")
        print("1. 회원가입")
        print("2. 로그인")
        print("3. 종료")
        choice = input("번호를 입력하세요: ")

        if choice == "1":
            sign_up()
        elif choice == "2":
            login()
        elif choice == "3":
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다. 다시 선택하세요.")
