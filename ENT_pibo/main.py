import sys
import os

# ENT_pibo 디렉토리 경로를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # '0': 모든 로그, '1': INFO 제거, '2': WARNING 제거, '3': ERROR만 표시

import absl.logging
absl.logging.set_verbosity(absl.logging.ERROR)

from features.auth.login import sign_up, login
from features.workouts.squat import run_squat
from features.workouts.bench import run_bench
from features.workouts.deadlift import run_deadlift
from features.motivation.ranking.rank import print_user_ranking 

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
            run_squat(user_id)  #스쿼트 실행
        elif choice == "2":
            print("데드리프트 감지 시작!")
            run_deadlift(user_id)
        elif choice == "3":
            print("벤치프레스 감지 준비 중...")  #나중에 추가할 부분
        elif choice == "4":
            print("로그아웃되었습니다.")
            break
        else:
            print("잘못된 입력입니다. 다시 선택하세요.")

if __name__ == "__main__":
    main()
