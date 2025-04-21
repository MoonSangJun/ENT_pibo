import cv2
import mediapipe as mp
from utils.pose_utils import calculate_2d_angle
from utils.firebase_utils import update_workout_score
from features.communication.tts_stt_mac import speak
from utils.video_overlay_utils import all_landmarks_visible, draw_info_overlay

def run_squat(user_id):
    cap = cv2.VideoCapture(1)
    counter, set_counter = 0, 0
    stage = None
    score_list = []
    last_score = None
    min_squat_angle = None
    last_feedback = None
    mp_pose_instance = mp.solutions.pose

    required_landmarks = [23, 25, 27, 24, 26, 28]

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
                        hip = [landmarks[23].x, landmarks[23].y]
                        knee = [landmarks[25].x, landmarks[25].y]
                        ankle = [landmarks[27].x, landmarks[27].y]
                        angle = calculate_2d_angle(hip, knee, ankle)

                        if angle < 120:
                            if stage != "down":
                                stage = "down"
                                min_squat_angle = angle
                            else:
                                min_squat_angle = min(min_squat_angle, angle)
                        elif angle > 170 and stage == "down":
                            stage = "up"
                            counter += 1
                            score = max(0, 100 - abs(min_squat_angle - 90) * 0.3)
                            last_score = int(score)
                            score_list.append(last_score)

                            feedback = (
                                "조금만 덜 앉아도 괜찮아요." if min_squat_angle <= 75
                                else "조금 더 앉아주세요." if min_squat_angle >= 90
                                else "좋은 자세예요!"
                            )
                            if feedback != last_feedback:
                                speak(feedback)
                                last_feedback = feedback

                            if counter >= 12:
                                avg_score = int(sum(score_list) / len(score_list))
                                speak(f"세트 완료! 평균 점수는 {avg_score}점입니다.")
                                update_workout_score(user_id, "squat", avg_score, reps=12, sets=1)
                                counter = 0
                                score_list = []
                                set_counter += 1
                    except Exception as e:
                        print(e)

                image = draw_info_overlay(image, counter, set_counter, last_score, ready)
                if counter == 0 and last_score:
                    cv2.putText(image, f"Set Score: {last_score}", (250, 250),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                mp.solutions.drawing_utils.draw_landmarks(image, results.pose_landmarks, mp_pose_instance.POSE_CONNECTIONS)
            else:
                image = draw_info_overlay(image, counter, set_counter, last_score, False)

            cv2.imshow("Squat Assistant", image)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()