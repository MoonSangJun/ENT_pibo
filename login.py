import firebase_admin
from firebase_admin import credentials, auth, firestore
import random

# Firebase 초기화
cred = credentials.Certificate("ent-pibo-firebase-adminsdk-fbsvc-07ff86926b.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# 4자리 중복 없는 사용자 ID 생성 함수
def generate_unique_id():
    while True:
        user_id = str(random.randint(1000, 9999))
        doc_ref = db.collection("users").document(user_id)
        if not doc_ref.get().exists:
            return user_id

# 회원가입 함수
def sign_up():
    name = input("이름을 입력하세요: ")
    password = input("비밀번호를 입력하세요 (6자리 숫자): ")

    if len(password) != 6 or not password.isdigit():
        print("비밀번호는 6자리 숫자여야 합니다.")
        return None

    email = f"{name}@example.com"  # Firebase 요구 사항

    try:
        user = auth.create_user(email=email, password=password)

        # 중복되지 않는 4자리 ID 생성
        user_id = generate_unique_id()

        # Firestore에 사용자 정보 저장
        user_doc = db.collection("users").document(user_id)
        user_doc.set({
            "name": name,
            "email": email
        })

        # 하위 컬렉션 생성
        user_doc.collection("bench").document("init").set({})
        user_doc.collection("squat").document("init").set({})
        user_doc.collection("deadlift").document("init").set({})

        print(f"회원가입 성공! {name}님 환영합니다! 당신의 ID는 {user_id}입니다.")  
        return user_id
    except Exception as e:
        print(f"회원가입 실패: {e}")
        return None

# 로그인 함수 (4자리 고유번호 기반)
def login():
    user_id = input("고유번호 4자리를 입력하세요: ")

    if len(user_id) != 4 or not user_id.isdigit():
        print("고유번호는 4자리 숫자여야 합니다.")
        return None

    user_doc = db.collection("users").document(user_id).get()
    
    if user_doc.exists:
        user_data = user_doc.to_dict()
        print(f"로그인 성공! {user_data['name']}님 환영합니다! (ID: {user_id})")
        return user_id
    else:
        print("해당 ID를 가진 사용자가 존재하지 않습니다.")
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
