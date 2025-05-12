import cv2
import mediapipe as mp
from datetime import datetime
from utils.pose_utils import calculate_2d_angle
from utils.firebase_utils import update_workout_score
from utils.firebase_utils import get_user_difficulty
from utils.video_overlay_utils import all_landmarks_visible, draw_info_overlay
from features.communication.tts_stt import speak_feedback

def run_bench(user_id, difficulty):
    difficulty = get_user_difficulty(user_id)
    reps_per_set = {"easy": 8, "normal": 12, "hard": 15}.get(difficulty, 12)
    cap = cv2.VideoCapture(1)
    counter, set_counter = 0, 0
    total_reps, total_exp = 0, 0
    score_list = []
    stage = None
    last_score = None
    start_time = datetime.now()
    required_landmarks = [11, 13, 15, 12, 14, 16]
    mp_pose_instance = mp.solutions.pose

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

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                ready = all_landmarks_visible(landmarks, required_landmarks)

                if ready:
                    try:
                        left_angle = calculate_2d_angle([landmarks[11].x, landmarks[11].y],
                                                        [landmarks[13].x, landmarks[13].y],
                                                        [landmarks[15].x, landmarks[15].y])
                        right_angle = calculate_2d_angle([landmarks[12].x, landmarks[12].y],
                                                         [landmarks[14].x, landmarks[14].y],
                                                         [landmarks[16].x, landmarks[16].y])
                        avg_angle = (left_angle + right_angle) / 2
                        accuracy = max(0, 100 - abs(avg_angle - 160))
                        last_score = int(accuracy)

                        if left_angle < 90 and right_angle < 90:
                            stage = "down"
                        elif left_angle > 140 and right_angle > 140 and stage == "down":
                            stage = "up"
                            counter += 1
                            score_list.append(last_score)
                            total_reps += 1
                            total_exp += last_score

                            if counter >= reps_per_set:
                                avg_score = int(sum(score_list) / len(score_list))
                                speak_feedback(f"세트 완료! 평균 점수는 {avg_score}점입니다.")
                                set_counter += 1
                                counter = 0
                                score_list = []
                                stage = None
                    except Exception as e:
                        print(e)

                image = draw_info_overlay(image, counter, set_counter, last_score, ready)
                if counter == 0 and last_score:
                    cv2.putText(image, f"Set Score: {last_score}", (250, 250),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                mp.solutions.drawing_utils.draw_landmarks(image, results.pose_landmarks, mp_pose_instance.POSE_CONNECTIONS)
            else:
                image = draw_info_overlay(image, counter, set_counter, last_score, False)

            cv2.imshow("Bench Tracker", image)

            key = cv2.waitKey(10) & 0xFF
            if key == ord(' '):  # 수동 디버그
                counter += 1
                score_list.append(100)
                last_score = 100
                total_reps += 1
                total_exp += 100

                if counter >= reps_per_set:
                    avg_score = int(sum(score_list) / len(score_list))
                    speak_feedback(f"세트 완료! 평균 점수는 {avg_score}점입니다.")
                    set_counter += 1
                    counter = 0
                    score_list = []
                    stage = None

            elif key == ord('q'):
                end_time = datetime.now()
                if total_reps > 0:
                    update_workout_score(user_id=user_id,
                                         workout_type="bench",
                                         score=total_exp,
                                         reps=total_reps,
                                         start_time=start_time,
                                         end_time=end_time)
                break

    cap.release()
    cv2.destroyAllWindows()
