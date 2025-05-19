import cv2
import mediapipe as mp
from datetime import datetime
from utils.pose_utils import calculate_2d_angle
from utils.firebase_utils import update_workout_score, get_user_difficulty, get_user_pibo_mode
from utils.video_overlay_utils import all_landmarks_visible, draw_info_overlay
from features.communication.tts_stt import speak_feedback

def run_squat(user_id, difficulty):
    pibo_mode = get_user_pibo_mode(user_id)
    difficulty = get_user_difficulty(user_id)
    reps_per_set = {"easy": 8, "normal": 12, "hard": 15}.get(difficulty, 12)

    cap = cv2.VideoCapture(0)
    counter, set_counter = 0, 0
    total_reps, total_exp = 0, 0
    score_list = []
    stage = None
    last_score = None
    min_down_angle = None
    start_time = datetime.now()
    exit_pressed_once = False
    exit_time = None

    required_landmarks = [23, 25, 27, 24, 26, 28]
    mp_pose_instance = mp.solutions.pose

    feedback_flags = {
        "greeted": False,
        "encouraged": False,
        "visibility_prompted": False,
        "ready_prompted": False
    }

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

            if not feedback_flags["greeted"]:
                if pibo_mode == "friendly":
                    speak_feedback("스쿼트 시작합니다. 이번 운동도 잘 해낼거에요. 화이팅.")
                elif pibo_mode == "spartan":
                    speak_feedback("운동 시작이다. 자세 잡아라.")
                feedback_flags["greeted"] = True

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                visible = all_landmarks_visible(landmarks, required_landmarks)

                if not visible:
                    if not feedback_flags["visibility_prompted"]:
                        if pibo_mode == "friendly":
                            speak_feedback("몸 전체가 화면에 보이도록 서 주세요.")
                        elif pibo_mode == "spartan":
                            speak_feedback("화면에 신체가 다 보이게 서")
                        feedback_flags["visibility_prompted"] = True
                        feedback_flags["ready_prompted"] = False
                
                if visible:
                    feedback_flags["visibility_prompted"] = False
                    if not feedback_flags["ready_prompted"]:
                        if pibo_mode == "friendly":
                            speak_feedback("좋아요, 준비됐어요! 스쿼트를 시작하세요.")
                        elif pibo_mode == "spartan":
                            speak_feedback("자 이제 스쿼트 시작!")
                        feedback_flags["ready_prompted"] = True
                        
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

                        # ✅ 실시간 accuracy는 화면 표시용
                        accuracy = max(0, 100 - abs(avg_angle - 90))

                        if stage == "down" and avg_angle >= 130:
                            stage = "up"
                            counter += 1

                            # ✅ 실제 점수 계산: min_down_angle 기반
                            if min_down_angle is not None:
                                angle_diff = abs(min_down_angle - 90)
                                score = max(0, 100 - angle_diff)
                                last_score = int(score)
                                score_list.append(last_score)
                                total_reps += 1
                                total_exp += last_score

                                # 피드백
                                if min_down_angle < 75:
                                    speak_feedback("조금만 덜 앉아 주세요." if pibo_mode == "friendly" else "너무 앉았다 조금 덜 앉아봐")
                                elif min_down_angle > 95:
                                    speak_feedback("조금만 더 앉아 주세요." if pibo_mode == "friendly" else "그걸로 되겠어? 더 앉아")

                            min_down_angle = None

                            # 격려 타이밍
                            if counter >= int(reps_per_set * 0.7) and not feedback_flags["encouraged"]:
                                speak_feedback("좋아요! 거의 다 왔어요 조금만 더 힘내세요!" if pibo_mode == "friendly" else "하나 더! 아직 멀었어!")
                                feedback_flags["encouraged"] = True

                            # 세트 종료
                            if counter >= reps_per_set:
                                avg_score = int(sum(score_list) / len(score_list))
                                speak_feedback(
                                    f"세트 끝! 수고했어요~ 평균 점수는 {avg_score}점입니다." if pibo_mode == "friendly"
                                    else f"세트 완료다. 평균 점수는 {avg_score}점이다."
                                )
                                set_counter += 1
                                counter = 0
                                score_list = []
                                stage = None
                                feedback_flags["encouraged"] = False

                        elif avg_angle <= 120:
                            if stage != "down":
                                stage = "down"
                                min_down_angle = avg_angle
                            else:
                                if avg_angle < min_down_angle:
                                    min_down_angle = avg_angle
                                
                    except Exception as e:
                        print(e)        

                image = draw_info_overlay(image, counter, set_counter, last_score, visible)
                mp.solutions.drawing_utils.draw_landmarks(image, results.pose_landmarks, mp_pose_instance.POSE_CONNECTIONS)
            else:
                image = draw_info_overlay(image, counter, set_counter, int(accuracy), False)

            cv2.imshow("Squat Tracker", image)
            
            key = cv2.waitKey(10) & 0xFF

            if key == ord(' '):
                counter += 1
                score_list.append(100)
                last_score = 100
                total_reps += 1
                total_exp += 100

                if counter >= reps_per_set:
                    avg_score = int(sum(score_list) / len(score_list))
                    speak_feedback(
                        f"세트 끝! 수고했어요~ 평균 점수는 {avg_score}점입니다." if pibo_mode == "friendly"
                        else f"세트 완료다. 평균 점수는 {avg_score}점이다."
                    )
                    set_counter += 1
                    counter = 0
                    score_list = []
                    stage = None
                    feedback_flags["encouraged"] = False

            if key == ord('q'):
                if not exit_pressed_once:
                    speak_feedback(
                        "정말 종료하시겠어요? 한세트 더 해보는건 어떨까요?" if pibo_mode == "friendly"
                        else "고작 이걸로 운동 끝내게? 다시 원위치해"
                    )
                    exit_pressed_once = True
                    exit_time = datetime.now()
                elif (datetime.now() - exit_time).total_seconds() <= 3:
                    speak_feedback(
                        "수고하셨습니다! 운동을 종료합니다." if pibo_mode == "friendly"
                        else "운동 끝났다. 가도 좋다."
                    )
                    if total_reps > 0:
                        end_time = datetime.now()
                        update_workout_score(
                            user_id=user_id,
                            workout_type="squat",
                            score=total_exp,
                            reps=total_reps,
                            start_time=start_time,
                            end_time=end_time
                        )
                    break

    cap.release()
    cv2.destroyAllWindows()
