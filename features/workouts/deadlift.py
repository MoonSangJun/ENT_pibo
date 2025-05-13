import cv2
import mediapipe as mp
from datetime import datetime
from utils.pose_utils import calculate_2d_angle
from utils.firebase_utils import update_workout_score, get_user_difficulty, get_user_pibo_mode
from utils.video_overlay_utils import all_landmarks_visible, draw_info_overlay
from features.communication.tts_stt import speak_feedback

def run_deadlift(user_id, difficulty):
    pibo_mode = get_user_pibo_mode(user_id)
    difficulty = get_user_difficulty(user_id)
    reps_per_set = {"easy": 8, "normal": 12, "hard": 15}.get(difficulty, 12)

    cap = cv2.VideoCapture(1)
    counter, set_counter = 0, 0
    total_reps, total_exp = 0, 0
    score_list = []
    stage = None
    last_score = None
    start_time = datetime.now()
    required_landmarks = [23, 25, 27, 24, 26, 28]
    mp_pose_instance = mp.solutions.pose

    feedback_flags = {
        "greeted": False,
        "encouraged": False,
        "suggested_retry": False,
    }
    exit_pressed_once = False
    exit_time = None

    with mp_pose_instance.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # 인삿말
            if not feedback_flags["greeted"]:
                if pibo_mode == "friendly":
                    speak_feedback("데드리프트를 시작합니다. 준비되셨나요?")
                elif pibo_mode == "spartan":
                    speak_feedback("운동 시작이다. 자세 잡아라.")
                feedback_flags["greeted"] = True    

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                ready = all_landmarks_visible(landmarks, required_landmarks)

                if ready:
                    try:
                        left_angle = calculate_2d_angle(
                            [landmarks[23].x, landmarks[23].y],
                            [landmarks[25].x, landmarks[25].y],
                            [landmarks[27].x, landmarks[27].y]
                        )
                        right_angle = calculate_2d_angle(
                            [landmarks[24].x, landmarks[24].y],
                            [landmarks[26].x, landmarks[26].y],
                            [landmarks[28].x, landmarks[28].y]
                        )
                        avg_angle = (left_angle + right_angle) / 2
                        accuracy = max(0, 100 - abs(avg_angle - 180))
                        last_score = int(accuracy)

                        # 실시간 자세 피드백
                        if avg_angle < 130:
                            if pibo_mode == "friendly":
                                speak_feedback("허리를 살짝만 더 펴볼까요?")
                            elif pibo_mode == "spartan":
                                speak_feedback("허리 펴! 자세 흐트러졌어!")
                        elif avg_angle > 190:
                            if pibo_mode == "friendly":
                                speak_feedback("조금만 덜 젖혀도 좋아요!")
                            elif pibo_mode == "spartan":
                                speak_feedback("뒤로 젖히지 마! 중심 잡아!")

                        # 자세 단계 판단
                        if avg_angle < 100:
                            stage = "down"
                        elif avg_angle > 170 and stage == "down":
                            stage = "up"
                            counter += 1
                            score_list.append(last_score)
                            total_reps += 1
                            total_exp += last_score

                            # 세트 후반부 응원
                            if counter >= int(reps_per_set * 0.7) and not feedback_flags["encouraged"]:
                                if pibo_mode == "friendly":
                                    speak_feedback("좋아요! 조금만 더 힘내세요!")
                                elif pibo_mode == "spartan":
                                    speak_feedback("더 열심히 해! 아직 멀었어!")
                                feedback_flags["encouraged"] = True

                            # 세트 완료 시
                            if counter >= reps_per_set:
                                avg_score = int(sum(score_list) / len(score_list))
                                if pibo_mode == "friendly":
                                    speak_feedback(f"세트 끝! 수고했어요~ 평균 점수는 {avg_score}점입니다.")
                                elif pibo_mode == "spartan":
                                    speak_feedback(f"세트 완료다. 점수는 {avg_score}점이다.")
                                set_counter += 1
                                counter = 0
                                score_list = []
                                stage = None
                                feedback_flags["encouraged"] = False

                    except Exception as e:
                        print(e)

                image = draw_info_overlay(image, counter, set_counter, last_score, ready)
                mp.solutions.drawing_utils.draw_landmarks(image, results.pose_landmarks, mp_pose_instance.POSE_CONNECTIONS)
            else:
                image = draw_info_overlay(image, counter, set_counter, last_score, False)

            cv2.imshow("Deadlift Tracker", image)

            key = cv2.waitKey(10) & 0xFF

            # 테스트용 강제 카운트
            if key == ord(' '):
                counter += 1
                score_list.append(100)
                last_score = 100
                total_reps += 1
                total_exp += 100

                if counter >= reps_per_set:
                    avg_score = int(sum(score_list) / len(score_list))
                    if pibo_mode == "friendly":
                        speak_feedback(f"세트 끝! 수고했어요~ 평균 점수는 {avg_score}점입니다.")
                    elif pibo_mode == "spartan":
                        speak_feedback(f"세트 완료다. 점수는 {avg_score}점이다.")
                    set_counter += 1
                    counter = 0
                    score_list = []
                    stage = None
                    feedback_flags["encouraged"] = False

            # 종료 로직
            if key == ord('q'):
                if not exit_pressed_once:
                    if pibo_mode == "friendly":
                        speak_feedback("정말 종료하시겠어요? 한 번 더 누르면 종료합니다.")
                    elif pibo_mode == "spartan":
                        speak_feedback("끝낼 거면 다시 눌러라.")
                    exit_pressed_once = True
                    exit_time = datetime.now()
                elif (datetime.now() - exit_time).total_seconds() <= 3:
                    if pibo_mode == "friendly":
                        speak_feedback("수고하셨습니다! 운동을 종료합니다.")
                    elif pibo_mode == "spartan":
                        speak_feedback("운동 끝났다. 나가도 좋다.")
                    if total_reps > 0:
                        end_time = datetime.now()
                        update_workout_score(
                            user_id=user_id,
                            workout_type="deadlift",
                            score=total_exp,
                            reps=total_reps,
                            start_time=start_time,
                            end_time=end_time
                        )
                    break

    cap.release()
    cv2.destroyAllWindows()
