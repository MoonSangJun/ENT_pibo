import cv2
import mediapipe as mp
import numpy as np
from datetime import datetime
from firebase_config import db
from dailyquest import check_daily_quest

# MediaPipe 초기화
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# 각도 계산 함수
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

# 정확도 점수 계산 (감점 완화)
def calculate_accuracy_score(squat_angle):
    ideal_angle = 90
    error = abs(squat_angle - ideal_angle)
    score = max(0, 100 - error * 1)  # 감점 비율 조정가능
    return int(score)

# Firebase에 점수 저장
def update_workout_score(user_id, workout_type, score, date=None):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    doc_ref = db.collection("users").document(user_id).collection(workout_type).document(date)
    doc = doc_ref.get()
    if doc.exists:
        prev_data = doc.to_dict()
        prev_score = prev_data.get("weight", 0)
        prev_sets = prev_data.get("sets", 0)
    else:
        prev_score = 0
        prev_sets = 0

    new_score = prev_score + score
    new_sets = prev_sets + 1

    doc_ref.set({
        "weight": new_score,
        "sets": new_sets
    })

    # total에도 반영
    total_ref = db.collection("users").document(user_id).collection("total").document(date)
    total_doc = total_ref.get()
    if total_doc.exists:
        prev_total = total_doc.to_dict().get("weight", 0)
    else:
        prev_total = 0
    total_ref.set({
        "weight": prev_total + score
    })

# 메인 실행 함수
def run_squat(user_id):
    cap = cv2.VideoCapture(0)
    counter = 0
    stage = None
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
                if not results.pose_landmarks:
                    continue

                landmarks = results.pose_landmarks.landmark

                required_points = [
                    mp_pose.PoseLandmark.LEFT_HIP.value,
                    mp_pose.PoseLandmark.LEFT_KNEE.value,
                    mp_pose.PoseLandmark.LEFT_ANKLE.value
                ]

                if not all(landmarks[i].visibility > 0.5 for i in required_points):
                    continue

                hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                       landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                        landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

                squat_angle = calculate_angle(hip, knee, ankle)
                accuracy = calculate_accuracy_score(squat_angle)

                # 화면에 표시만 (카운트 외에는 로그 X)
                cv2.putText(image, f'SQUAT ANGLE: {int(squat_angle)}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(image, f'ACCURACY: {accuracy}', (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                #down -> up 전환 기준으로만 카운트
                if squat_angle < 100 and stage != "down":
                    stage = "down"

                elif squat_angle > 150 and stage == "down":
                    stage = "up"
                    counter += 1
                    score_list.append(accuracy)
                    print(f"✅ {counter}회 완료 (정확도: {accuracy})")

                    if counter % 12 == 0:
                        set_score = int(sum(score_list) / len(score_list))
                        print(f"🏁 세트 완료! 평균 점수: {set_score}")
                        update_workout_score(user_id, "squat", set_score)
                        update_workout_score(user_id, "total", set_score)
                        check_daily_quest(user_id)
                        score_list = []

            except Exception:
                pass

            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            cv2.imshow("Squat Assistant", image)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()