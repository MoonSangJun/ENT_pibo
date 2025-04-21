import cv2
import mediapipe as mp
from utils.pose_utils import calculate_2d_angle
from utils.firebase_utils import update_workout_score
from utils.video_overlay_utils import all_landmarks_visible, draw_info_overlay

def run_deadlift(user_id):
    cap = cv2.VideoCapture(1)
    counter, set_counter = 0, 0
    stage = "up"
    score_list = []
    last_score = None
    mp_pose_instance = mp.solutions.pose

    required_landmarks = [11, 23, 25, 12, 24, 26, 15, 16]

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
                                                        [landmarks[23].x, landmarks[23].y],
                                                        [landmarks[25].x, landmarks[25].y])
                        right_angle = calculate_2d_angle([landmarks[12].x, landmarks[12].y],
                                                         [landmarks[24].x, landmarks[24].y],
                                                         [landmarks[26].x, landmarks[26].y])
                        avg_angle = (left_angle + right_angle) / 2
                        accuracy = max(0, 100 - abs(avg_angle - 180))
                        last_score = int(accuracy)

                        left_hand_low = landmarks[15].y > landmarks[25].y
                        right_hand_low = landmarks[16].y > landmarks[26].y

                        if avg_angle < 70 and (left_hand_low or right_hand_low) and stage == "up":
                            stage = "down"
                        elif avg_angle > 160 and not left_hand_low and not right_hand_low and stage == "down":
                            stage = "up"
                            counter += 1
                            score_list.append(last_score)

                            if counter >= 12:
                                avg_score = int(sum(score_list) / len(score_list))
                                update_workout_score(user_id, "deadlift", avg_score, reps=12, sets=1)
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

            cv2.imshow("Deadlift Tracker", image)
            
            key = cv2.waitKey(10) & 0xFF
            if key == ord(' '):
                counter += 1
                score_list.append(100)
                last_score = 100

            # 추가
            if counter >= 12:
                avg_score = int(sum(score_list) / len(score_list)) if score_list else 100
                update_workout_score(user_id, "deadlift", avg_score)
                counter = 0
                score_list = []
                set_counter += 1
                                                            
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()