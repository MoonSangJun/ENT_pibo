from login import sign_up, login
from squat import run_squat
from rank import print_user_ranking 
from bench import start_bench_tracking
from deadlift import run_deadlift
#일단은 스쿼트만 나중에 더 추가해야할듯

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
        print("4. 랭킹보기")
        print("5. 로그아웃")
        choice = input("운동 번호를 선택하세요: ")

        if choice == "1":
            run_squat(user_id)
        elif choice == "2":
            run_deadlift(user_id)
        elif choice == "3":
            start_bench_tracking(user_id)
        elif choice == "4":
            print_user_ranking()
        elif choice == "5":
            print("로그아웃되었습니다.")
            break
        else:
            print("잘못된 입력입니다. 다시 선택하세요.")

if __name__ == "__main__":
    main()