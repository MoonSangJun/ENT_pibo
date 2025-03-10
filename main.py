from login import sign_up, login
import squat  # 스쿼트 모듈 (나중에 데드리프트, 벤치프레스 추가)

def main():
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
                select_exercise(user_id)
        elif choice == "3":
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다. 다시 선택하세요.")

def select_exercise(user_id):
    while True:
        print("\n운동 선택")
        print("1. 스쿼트")
        print("2. 데드리프트")
        print("3. 벤치프레스")
        print("4. 로그아웃")
        choice = input("운동 번호를 선택하세요: ")

        if choice == "1":
            print("스쿼트 감지 시작!")
            squat.start_squat_tracking(user_id)  # 스쿼트 감지 실행
        elif choice == "2":
            print("데드리프트 감지 준비 중...")  # 나중에 추가할 부분
        elif choice == "3":
            print("벤치프레스 감지 준비 중...")  # 나중에 추가할 부분
        elif choice == "4":
            print("로그아웃되었습니다.")
            break
        else:
            print("잘못된 입력입니다. 다시 선택하세요.")

if __name__ == "__main__":
    main()
