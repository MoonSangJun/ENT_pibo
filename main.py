from features.auth.login import sign_up, login
from features.workouts.squat import run_squat
from features.motivation.rank import print_user_ranking 
from features.workouts.bench import run_bench
from features.workouts.deadlift import run_deadlift
from features.auth.qr_login import login_with_qr

from utils.listen import listen_to_question
from utils.chatgpt import ask_gpt, speak_text
from features.communication.tts_sender import send_feedback_signal_to_pibo
from features.communication.send_mp3_pibo import send_tts
from features.communication.send_montion_pibo import send_motion_command

from features.communication.tts_stt_mac import speak 



#일단은 스쿼트만 나중에 더 추가해야할듯
def main():
    print("\n=== ENT_Pibo 시작 ===\n")
    speak("큐알 코드를 카메라에 대주세요")
    
    while True:
        #user_id = login_with_qr()a
        user_id = login()
        if user_id:
            voice_mode(user_id)
        



    


    # while True:
    #     print("\n1. 회원가입\n2. 로그인\n3. 종료")
    #     choice = input("번호를 입력하세요: ")

    #     if choice == "1":
    #         sign_up()
    #     elif choice == "2":
    #         user_id = login()
    #         if user_id:
    #             voice_mode(user_id)
    #     elif choice == "3":
    #         print("프로그램 종료합니다.")
    #         break
    #     else:
    #         print("잘못된 입력입니다. 다시 선택하세요.")

def voice_mode(user_id):
    #send_tts("로그인 되었습니다")
    send_motion_command("m_wakeup")
    speak("로그인 되었습니다!!")
    print("\n🎤 음성 모드 시작합니다!")
    print(" - '안녕' 이라고 부르면 대화 시작")
    speak("안녕' 이라고 부르면 대화가 시작되고, 스쿼트, 벤치프레스, 데드리프트 중 하나를 말하면 운동을 시작합니다.")
    #send_tts("안녕' 이라고 부르면 대화가 시작되고, 스쿼트, 벤치프레스, 데드리프트 중 하나를 말하면 운동을 시작합니다.")
    print(" - '스쿼트', '벤치프레스', '데드리프트' 를 말하면 운동 시작\n")

    while True:
        text = listen_to_question(timeout=3, phrase_time_limit=3)

        if text is None:
            continue

        if "안녕" in text:
            print("🧠 GPT 대화 모드 시작!")
            speak("안녕하세요! 무엇이든지 말씀해주세요!")
            question = listen_to_question(timeout=7, phrase_time_limit=10)
            if question:
                answer = ask_gpt(question)
                send_tts(answer)
                speak_text(answer)

        elif "스쿼트" in text:
            speak("스쿼트 운동을 시작합니다!")
            print("🏋️ 스쿼트 감지 시작합니다!")
            run_squat(user_id)

        elif "벤치프레스" or "벤치 프레스" in text:
            speak("벤치프레스 운동을 시작합니다.")
            print("🏋️ 벤치프레스 감지 시작합니다!")
            run_bench(user_id)

        elif "데드 리프트" or "데드리프트" in text:
            speak("데드리프트 운동을 시작합니다")
            print("🏋️ 데드리프트 감지 시작합니다!")
            run_deadlift(user_id)

        elif "종료" in text or "그만" in text:
            print("👋 음성 모드 종료합니다.")
            break

        else:
            print(f"⚡ '{text}' 인식했지만 명령어가 아님.")
            speak("다시 한번 정확히 말해주세요")

if __name__ == "__main__":
    main()



# import threading
# from features.workouts.squat import run_squat
# from features.workouts.bench import run_bench
# from features.workouts.deadlift import run_deadlift
# from utils.listen import listen_to_question
# from features.communication.tts_stt_mac import speak

# # 유저 ID는 로그인 이후 넘겨받는다고 가정
# user_id = "your_user_id"

# # 음성 처리 스레드
# def voice_listener():
#     while True:
#         text = listen_to_question(timeout=3, phrase_time_limit=3)
#         if not text:
#             continue
#         print(f"[음성 인식]: {text}")
#         handle_command(text)

# # 터미널 입력 처리 스레드
# def terminal_listener():
#     while True:
#         command = input("⌨️ 명령 입력: ").strip()
#         handle_command(command)

# # 명령어 공통 처리
# def handle_command(text):
#     if "스쿼트" in text:
#         speak("스쿼트 운동을 시작합니다!")
#         run_squat(user_id)

#     elif "벤치프레스" in text or "벤치 프레스" in text:
#         speak("벤치프레스 운동을 시작합니다!")
#         run_bench(user_id)

#     elif "데드리프트" in text or "데드 리프트" in text:
#         speak("데드리프트 운동을 시작합니다!")
#         run_deadlift(user_id)

#     elif "종료" in text or "그만" in text:
#         speak("프로그램을 종료합니다.")
#         exit()

#     else:
#         speak("알 수 없는 명령입니다. 다시 말씀해주세요.")

# # 메인 실행
# if __name__ == "__main__":
#     print("🧠 음성 및 텍스트 명령 모드 시작!")
#     speak("스쿼트, 벤치프레스, 데드리프트 중 하나를 말씀하거나 입력해주세요!")

#     # 병렬로 실행
#     threading.Thread(target=voice_listener, daemon=True).start()
#     threading.Thread(target=terminal_listener, daemon=True).start()

#     # 메인 스레드는 대기만
#     threading.Event().wait()
