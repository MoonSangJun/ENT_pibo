import cv2
import mediapipe as mp
import threading
from datetime import datetime
from utils.pose_utils import calculate_2d_angle
from utils.firebase_utils import update_workout_score
from utils.firebase_utils import get_user_difficulty
from utils.video_overlay_utils import all_landmarks_visible, draw_info_overlay
from features.video.camera_receive import get_frame_from_pibo
from features.communication.tts_sender import send_feedback_signal_to_pibo
from features.communication.tts_stt_mac import speak 
from features.communication.send_montion_pibo import send_motion_command
import speech_recognition as sr


def monitor_for_stop():
    """ 음성으로 '종료'를 감지하는 스레드 함수 """
    global stop_exercise
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("[음성 감지] '종료' 명령 대기 중...")

    while not stop_exercise:
        with mic as source:
            try:
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                command = recognizer.recognize_google(audio, language="ko-KR")
                print(f"[음성 인식 결과] {command}")

                if "종료" in command:
                    print("[종료 감지] 운동 종료를 시작합니다.")
                    stop_exercise = True
                    break

            except Exception:
                continue


def run_deadlift(user_id, difficulty):
    global stop_exercise
    stop_exercise = False 

    threading.Thread(target=monitor_for_stop, daemon=True).start()


    difficulty = get_user_difficulty(user_id)
    reps_per_set = {"easy": 8, "normal": 12, "hard": 15}.get(difficulty, 12)
    counter, set_counter = 0, 0
    total_reps, total_exp = 0, 0
    score_list = []
    stage = None
    last_score = None
    start_time = datetime.now()
    required_landmarks = [23, 25, 27, 24, 26, 28]
    mp_pose_instance = mp.solutions.pose

    frame_generator = get_frame_from_pibo()

    with mp_pose_instance.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        for frame in frame_generator:
            if stop_exercise:
                print("[운동 강제 종료 감지]")
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

                        if avg_angle < 100:
                            stage = "down"
                        elif avg_angle > 170 and stage == "down":
                            stage = "up"
                            counter += 1
                            score_list.append(last_score)
                            total_reps += 1
                            total_exp += last_score

                            if counter >= reps_per_set:
                                avg_score = int(sum(score_list) / len(score_list))
                                speak(f"세트 완료! 평균 점수는 {avg_score}점입니다.")
                                set_counter += 1
                                counter = 0
                                score_list = []
                                stage = None
                    except Exception as e:
                        print(e)

                image = draw_info_overlay(image, counter, set_counter, last_score, ready)
                mp.solutions.drawing_utils.draw_landmarks(image, results.pose_landmarks, mp_pose_instance.POSE_CONNECTIONS)
            else:
                image = draw_info_overlay(image, counter, set_counter, last_score, False)

            cv2.imshow("Deadlift Tracker", image)

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
                    
            if key == ord('q'):
                end_time = datetime.now()
                if total_reps > 0:
                    update_workout_score(user_id=user_id,
                                         workout_type="deadlift",
                                         score=total_exp,
                                         reps=total_reps,
                                         start_time=start_time,
                                         end_time=end_time)
                break


    cv2.destroyAllWindows()