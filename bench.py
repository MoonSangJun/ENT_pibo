import cv2
import mediapipe as mp
import numpy as np
import time
from datetime import datetime
import random
from dailyquest import check_daily_quest
from tts_stt import speak_feedback
import threading
import os
from firebase_config import db

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180.0 else angle

def update_firebase_set(user_id, exercise):
    today = datetime.today().strftime('%Y-%m-%d')
    doc_ref = db.collection("users").document(user_id).collection(exercise).document(today)
    doc = doc_ref.get()
    if doc.exists:
        current_set = doc.to_dict().get("sets", 0)
        doc_ref.update({"sets": current_set + 1})
    else:
        doc_ref.set({"sets": 1})

def update_firebase_total_score(user_id, score):
    exp_ref = db.collection("users").document(user_id).collection("total").document("exp")
    exp_doc = exp_ref.get()
    if exp_doc.exists:
        current_score = exp_doc.to_dict().get("score", 0)
        exp_ref.update({"score": current_score + score})
    else:
        exp_ref.set({"score": score})

def play_feedback(text):
    def run_tts():
        speak_feedback(text)
    threading.Thread(target=run_tts, daemon=True).start()

def start_bench_tracking(user_id):
    cap = cv2.VideoCapture(0)
    exercise_type = "bench"

    counter = 0
    stage = None
    prev_stage = None
    stage_start_time = time.time()
    last_feedback_time = time.time() - 10

    max_angle = 0
    min_angle = 180

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark

                shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                angle = calculate_angle(shoulder, elbow, wrist)
                max_angle = max(max_angle, angle)
                min_angle = min(min_angle, angle)

                if angle > 140:
                    new_stage = "up"
                elif angle < 40:
                    new_stage = "down"
                else:
                    new_stage = stage

                if new_stage != stage:
                    stage_start_time = time.time()
                elif time.time() - stage_start_time > 5 and time.time() - last_feedback_time > 10:
                    if stage == "down":
                        play_feedback("팔을 더 뻗으세요")
                    elif stage == "up":
                        play_feedback("팔을 더 내리세요")
                    last_feedback_time = time.time()

                stage = new_stage

                if stage == "down" and prev_stage == "up":
                    counter += 1
                    print(f"운동 횟수: {counter}")

                    if counter % 12 == 0:
                        print(f"한 세트 완료! 최고 각도: {max_angle:.2f}, 최저 각도: {min_angle:.2f}")

                        score = 0
                        if max_angle >= 160 and min_angle <= 20:
                            score = random.randint(80, 100)
                        elif max_angle >= 150 and min_angle <= 30:
                            score = random.randint(70, 80)
                        elif max_angle >= 140 and min_angle <= 40:
                            score = random.randint(60, 70)
                        else:
                            score = random.randint(40, 60)

                        print(f"부여된 점수: {score}")
                        play_feedback(f"한 세트 완료! 부여된 점수는 {score}점입니다.")
                        update_firebase_set(user_id, exercise_type)
                        update_firebase_total_score(user_id, score)
                        check_daily_quest(user_id)
                        max_angle = 0
                        min_angle = 180

                prev_stage = stage
            except:
                pass

            cv2.rectangle(image, (0, 0), (300, 100), (245, 117, 16), -1)
            cv2.putText(image, 'REPS', (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, str(counter % 12), (15, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

            cv2.putText(image, 'STAGE', (100, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, stage if stage else "", (100, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            cv2.imshow('Mediapipe Feed', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
