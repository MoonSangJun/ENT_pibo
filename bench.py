import cv2
import mediapipe as mp
import numpy as np
import time
from datetime import datetime
import random
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase 초기화 (이미 초기화된 경우 예외 처리)
if not firebase_admin._apps:
    cred = credentials.Certificate("ent-pibo-firebase-adminsdk-fbsvc-07ff86926b.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle

def update_firebase_count(user_id, exercise, count):
    today_date = datetime.today().strftime('%Y-%m-%d')
    doc_ref = db.collection("users").document(user_id).collection(exercise).document(today_date)
    doc = doc_ref.get()

    if doc.exists:
        current_count = doc.to_dict().get("reps", 0)
        new_count = current_count + count
        doc_ref.update({"reps": new_count})
    else:
        doc_ref.set({"reps": count})

def store_score(user_id, exercise, score):
    today_date = datetime.today().strftime('%Y-%m-%d')
    score_ref = db.collection("users").document(user_id).collection(exercise).document(today_date)

    score_ref.set({
        "score": score
    }, merge=True)

def start_bench_tracking(user_id):
    cap = cv2.VideoCapture(0)
    exercise_type = "bench"

    counter = 0
    stage = None
    prev_stage = None
    feedback = ""
    stage_start_time = time.time()

    max_angle = 0
    min_angle = 180
    score_list = []

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
                elif angle < 20:
                    new_stage = "down"
                else:
                    new_stage = stage

                if new_stage != stage:
                    stage_start_time = time.time()
                    feedback = ""

                elif time.time() - stage_start_time > 5:
                    feedback = "팔을 더 크게 움직이세요"

                stage = new_stage

                if stage == "down" and prev_stage == "up":
                    counter += 1
                    print(f"운동 횟수: {counter}")
                    update_firebase_count(user_id, exercise_type, 1)

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

                        score_list.append(score)
                        store_score(user_id, exercise_type, score)
                        print(f"부여된 점수: {score}")

                        max_angle = 0
                        min_angle = 180

                prev_stage = stage

            except:
                pass

            # 화면 출력
            cv2.rectangle(image, (0, 0), (300, 100), (245, 117, 16), -1)
            cv2.putText(image, 'REPS', (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, str(counter), (15, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

            cv2.putText(image, 'STAGE', (100, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, stage if stage else "", (100, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

            cv2.putText(image, feedback, (10, 450),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                      mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                      mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))

            cv2.imshow('Mediapipe Feed', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
