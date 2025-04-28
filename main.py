from features.auth.login import sign_up, login
from features.workouts.squat import run_squat
from features.motivation.rank import print_user_ranking 
from features.workouts.bench import run_bench
from features.workouts.deadlift import run_deadlift
from features.auth.qr_login import login_with_qr

from utils.listen import listen_to_question
from utils.chatgpt import ask_gpt, speak_text
from features.communication.tts_sender import send_feedback_signal_to_pibo
from features.communication.send_mp3_pibo import send_tts_mp3_to_pibo

from features.communication.tts_stt_mac import speak 





#일단은 스쿼트만 나중에 더 추가해야할듯
def main():
    print("\n=== ENT_Pibo 시작 ===\n")
    speak("큐알 코드를 카메라에 대주세요")
    
    while True:
        user_id = login_with_qr()
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
    speak("로그인 되었습니다!!")
    print("\n🎤 음성 모드 시작합니다!")
    print(" - '파이보야' 라고 부르면 대화 시작")
    print(" - '스쿼트', '벤치프레스', '데드리프트' 를 말하면 운동 시작\n")

    while True:
        text = listen_to_question(timeout=3, phrase_time_limit=3)

        if text is None:
            continue

        if "안녕" in text:
            print("🧠 GPT 대화 모드 시작!")
            question = listen_to_question(timeout=7, phrase_time_limit=10)
            if question:
                answer = ask_gpt(question)
                send_tts_mp3_to_pibo(answer)
                speak_text(answer)

        elif "스쿼트" in text:
            speak("스쿼트 운동을 시작합니다!")
            print("🏋️ 스쿼트 감지 시작합니다!")
            run_squat(user_id)

        elif "벤치 프레스" in text:
            print("🏋️ 벤치프레스 감지 시작합니다!")
            run_bench(user_id)

        elif "데드 리프트" in text:
            print("🏋️ 데드리프트 감지 시작합니다!")
            run_deadlift(user_id)

        elif "종료" in text or "그만" in text:
            print("👋 음성 모드 종료합니다.")
            break

        else:
            print(f"⚡ '{text}' 인식했지만 명령어가 아님.")

if __name__ == "__main__":
    main()