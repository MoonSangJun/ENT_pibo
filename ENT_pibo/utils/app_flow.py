from firebase_config import db
from utils.firebase_utils import update_user_settings, get_user_difficulty
from features.workouts.squat import run_squat
from features.workouts.bench import run_bench
from features.workouts.deadlift import run_deadlift
from features.auth.login import sign_up, login
from features.motivation.quests.dailyquest import create_daily_quest

def number_to_level(num, field_type):
    mappings = {
        "pibo_mode": {"1": "soft", "2": "normal", "3": "hard"},
        "difficulty": {"1": "easy", "2": "normal", "3": "hard"}
    }
    return mappings.get(field_type, {}).get(num)


def get_user_field(user_id, field_name):
    doc = db.collection("users").document(user_id).get()
    if doc.exists:
        return doc.to_dict().get(field_name, None)
    return None


def settings_menu(user_id):
    while True:
        print("\n[유저 설정]")
        print("1. 닉네임 변경")
        print("2. 파이보 모드 설정 [1: soft, 2: normal, 3: hard]")
        print("3. 그룹1 설정")
        print("4. 그룹2 설정")
        print("5. 난이도 설정 [1: easy, 2: normal, 3: hard]")
        print("6. 설정 종료")

        choice = input("옵션을 선택하세요: ").strip()

        if choice == "1":
            prev = get_user_field(user_id, "nickname")
            new = input("새 닉네임을 입력하세요: ").strip()
            if new:
                update_user_settings(user_id, nickname=new)
                if prev:
                    print(f"✅ 닉네임 변경: '{prev}' → '{new}'")
                else:
                    print(f"✅ 닉네임이 '{new}'로 설정되었습니다.")
        elif choice == "2":
            prev = get_user_field(user_id, "pibo_mode")
            print("파이보 모드 [1: soft, 2: normal, 3: hard]")
            selected = input("숫자를 입력하세요: ").strip()
            mode = number_to_level(selected, "pibo_mode")
            if mode:
                update_user_settings(user_id, pibo_mode=mode)
                if prev:
                    print(f"✅ 파이보 모드 변경: '{prev}' → '{mode}'")
                else:
                    print(f"✅ 파이보 모드가 '{mode}'로 설정되었습니다.")
            else:
                print("❌ 잘못된 입력입니다.")
        elif choice == "3":
            prev = get_user_field(user_id, "group1")
            group1 = input("그룹1 ID를 입력하세요: ").strip()
            if group1:
                update_user_settings(user_id, group1=group1)
                if prev:
                    print(f"✅ 그룹1 변경: '{prev}' → '{group1}'")
                else:
                    print(f"✅ 그룹1이 '{group1}'로 설정되었습니다.")
        elif choice == "4":
            prev = get_user_field(user_id, "group2")
            group2 = input("그룹2 ID를 입력하세요: ").strip()
            if group2:
                update_user_settings(user_id, group2=group2)
                if prev:
                    print(f"✅ 그룹2 변경: '{prev}' → '{group2}'")
                else:
                    print(f"✅ 그룹2가 '{group2}'로 설정되었습니다.")
        elif choice == "5":
            prev = get_user_field(user_id, "difficulty")
            print("난이도 [1: easy, 2: normal, 3: hard]")
            selected = input("숫자를 입력하세요: ").strip()
            diff = number_to_level(selected, "difficulty")
            if diff:
                update_user_settings(user_id, difficulty=diff)
                if prev:
                    print(f"✅ 난이도 변경: '{prev}' → '{diff}'")
                else:
                    print(f"✅ 난이도가 '{diff}'로 설정되었습니다.")
            else:
                print("❌ 잘못된 입력입니다.")
        elif choice == "6":
            print("설정 메뉴를 종료합니다.")
            break
        else:
            print("잘못된 입력입니다.")


def exercise_menu(user_id):
    create_daily_quest(user_id)
    difficulty = get_user_difficulty(user_id)
    
    while True:
        print("\n운동 선택")
        print("1. 스쿼트")
        print("2. 데드리프트")
        print("3. 벤치프레스")
        print("4. 설정 변경")
        print("5. 로그아웃")
        choice = input("옵션을 선택해주세요!: ")

        if choice == "1":
            print("스쿼트 감지 시작!")
            run_squat(user_id, difficulty)
        elif choice == "2":
            print("데드리프트 감지 시작!")
            run_deadlift(user_id, difficulty)
        elif choice == "3":
            print("벤치프레스 감지 시작!")
            run_bench(user_id, difficulty)
        elif choice == "4":
            settings_menu(user_id)
        elif choice == "5":
            print("로그아웃되었습니다.")
            break
        else:
            print("잘못된 입력입니다. 다시 선택하세요.")

def main_menu():
    while True:
        print("\nENT_Pibo")
        print("1. 회원가입")
        print("2. 로그인")
        print("3. 종료")
        choice = input("번호를 입력하세요: ")

        if choice == "1":
            sign_up()
        elif choice == "2":
            user_id = login()
            if user_id:
                exercise_menu(user_id)
        elif choice == "3":
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다. 다시 선택하세요.")