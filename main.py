from login import login


def main():
    print("ENT_Pibo 시작")
    
    #사용자 로그인
    email = input("이메일 입력: ")
    password = input("비밀번호 입력: ")
    user_id = login(email, password)
    
    if user_id:
        print(f"로그인 성공: {user_id}")
        
        # 자세 감지 실행
        # exercise_type = "squat"
        # accuracy = analyze_pose(exercise_type)
        
        # # 운동 데이터 업데이트
        # update_ranking(user_id, exercise_type, accuracy)

        # # TTS로 피드백 제공
        # speak("운동이 완료되었습니다! 랭킹을 확인하세요.")

if __name__ == "__main__":
    main()
