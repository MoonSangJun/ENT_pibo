import cv2
import mediapipe as mp
import numpy as np
import time
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime  # 날짜 처리를 위한 모듈 추가

# Firebase 초기화
cred = credentials.Certificate("ent-pibo-firebase-adminsdk-fbsvc-07ff86926b.json")  # Firebase 키 파일 경로 변경
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

cap = cv2.VideoCapture(0)

# Curl counter variables
counter = 0  
stage = None
prev_stage = None  
feedback = ""  
stage_start_time = time.time()  

exercise_type = "bench"  # 운동 종류를 bench, deadlift, squat 중 하나로 설정

def update_firebase_count(user_id, exercise, count):
    today_date = datetime.today().strftime('%Y-%m-%d')  # YYYY-MM-DD 형식 날짜 가져오기

    doc_ref = db.collection("users").document(user_id).collection(exercise).document(today_date)
    doc = doc_ref.get()
    
    if doc.exists:
        current_count = doc.to_dict().get("reps", 0)
        new_count = current_count + count
        doc_ref.update({"reps": new_count})
    else:
        doc_ref.set({"reps": count})

## Setup mediapipe instance
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

            cv2.putText(image, str(angle),
                        tuple(np.multiply(elbow, [640, 480]).astype(int)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

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
                if new_stage == "up":
                    feedback = "put down you arm more"
                elif new_stage == "down":
                    feedback = "push more"

            stage = new_stage

            if stage == "down" and prev_stage == "up":
                counter += 1
                print(f"운동 횟수: {counter}")

                # Firebase에 날짜별 업데이트
                update_firebase_count("user1", exercise_type, 1)
            
            prev_stage = stage  

        except:
            pass

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
