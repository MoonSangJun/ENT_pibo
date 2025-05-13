from firebase_config import db
from utils.firebase_utils import update_user_settings, get_user_difficulty
from features.workouts.squat import run_squat
from features.workouts.bench import run_bench
from features.workouts.deadlift import run_deadlift
from features.auth.login import sign_up, login
from features.motivation.quests.dailyquest import create_daily_quest

from features.communication.tts_stt_mac import speak
from features.communication.send_montion_pibo import send_motion_command
from utils.listen import listen_to_question
from utils.chatgpt import ask_gpt, speak_text



def number_to_level(num, field_type):
    mappings = {
        #수정된 부분(soft, normal, hard -> friendly, spartan)
        "pibo_mode": {"1": "friendly", "2": "spartan"}, 
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
        #수정된 부분(soft, normal, hard -> friendly, spartan)
        print("2. 파이보 모드 설정 [1: friendly, 2: spartan]")
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
            #수정된 부분(soft, normal, hard -> friendly, spartan)
            print("파이보 모드 [1: friendly, 2: spartan]")
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

    send_motion_command("m_wakeup")
    speak("로그인 되었습니다!!")
    print("\n🎤 음성 모드 시작합니다!")
    print(" - '안녕' 이라고 부르면 대화 시작")
    speak("안녕' 이라고 부르면 대화가 시작되고, 스쿼트, 벤치프레스, 데드리프트 중 하나를 말하면 운동을 시작합니다.")
    print(" - '스쿼트', '벤치프레스', '데드리프트' 를 말하면 운동 시작\n")

    while True:
        text = listen_to_question(timeout=3, phrase_time_limit=3)
        choice = input("번호를 입력하세요: ")

        if text is None:
            continue

        if "안녕" in text or choice == 1:
            print("🧠 GPT 대화 모드 시작!")
            speak("안녕하세요! 무엇이든지 말씀해주세요!")
            question = listen_to_question(timeout=7, phrase_time_limit=10)
            if question:
                answer = ask_gpt(question)
                #send_tts(answer)
                speak_text(answer)

        elif "스쿼트" in text or choice == 2:
            speak("스쿼트 운동을 시작합니다!")
            print("🏋️ 스쿼트 감지 시작합니다!")
            run_squat(user_id, difficulty)

        elif "벤치프레스" or "벤치 프레스" in text:
            speak("벤치프레스 운동을 시작합니다.")
            print("🏋️ 벤치프레스 감지 시작합니다!")
            run_bench(user_id, difficulty)

        elif "데드 리프트" or "데드리프트" in text:
            speak("데드리프트 운동을 시작합니다")
            print("🏋️ 데드리프트 감지 시작합니다!")
            run_deadlift(user_id, difficulty)

        elif "종료" in text or "그만" in text:
            print("👋 음성 모드 종료합니다.")
            break

        else:
            print(f"⚡ '{text}' 인식했지만 명령어가 아님.")
            speak("다시 한번 정확히 말해주세요")
    
    # while True:
    #     print("\n운동 선택")
    #     print("1. 스쿼트")
    #     print("2. 데드리프트")
    #     print("3. 벤치프레스")
    #     print("4. 설정 변경")
    #     print("5. 로그아웃")
    #     choice = input("옵션을 선택해주세요!: ")

    #     if choice == "1":
    #         print("스쿼트 감지 시작!")
    #         run_squat(user_id, difficulty)
    #     elif choice == "2":
    #         print("데드리프트 감지 시작!")
    #         run_deadlift(user_id, difficulty)
    #     elif choice == "3":
    #         print("벤치프레스 감지 시작!")
    #         run_bench(user_id, difficulty)
    #     elif choice == "4":
    #         settings_menu(user_id)
    #     elif choice == "5":
    #         print("로그아웃되었습니다.")
    #         break
    #     else:
    #         print("잘못된 입력입니다. 다시 선택하세요.")

def main_menu():
    print("\n=== ENT_Pibo 시작 ===\n")
    speak("큐알 코드를 카메라에 대주세요")


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