import cv2
import mediapipe as mp
import numpy as np
from datetime import datetime
from firebase_config import db

# Mediapipe 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# 각도 계산 함수
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

# 정확도 점수 계산
def calculate_accuracy_score(angle, stage):
    ideal_angle = 180  # 완전히 선 상태
    if stage == "up":
        # 동작을 처음 시작하는 경우 정확도를 0으로 설정
        return 0
    error = abs(angle - ideal_angle)
    score = max(0, 100 - error * 1)
    return int(score)

# Firebase에 점수 저장
def update_workout_score(user_id, workout_type, score, date=None):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    doc_ref = db.collection("users").document(user_id).collection(workout_type).document(date)
    doc = doc_ref.get()
    prev_data = doc.to_dict() if doc.exists else {}
    prev_score = prev_data.get("weight", 0)
    prev_sets = prev_data.get("sets", 0)

    new_score = prev_score + score
    new_sets = prev_sets + 1

    doc_ref.set({"weight": new_score, "sets": new_sets})

    # total에도 반영
    total_ref = db.collection("users").document(user_id).collection("total").document(date)
    total_doc = total_ref.get()
    prev_total = total_doc.to_dict().get("weight", 0) if total_doc.exists else 0
    total_ref.set({"weight": prev_total + score})

# 웹캠 실행
def run_deadlift(user_id):
    cap = cv2.VideoCapture(0)
    counter = 0  # 반복 횟수
    set_counter = 0  # 세트 수
    stage = "up"
    score_list = []
    
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
        
        try:
            if not results.pose_landmarks:
                continue
            
            landmarks = results.pose_landmarks.landmark
            left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y]
            left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP].y]
            left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y]
            left_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y]

            right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y]
            right_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y]
            right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y]
            right_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y]
            
            left_back_angle = calculate_angle(left_shoulder, left_hip, left_knee)
            right_back_angle = calculate_angle(right_shoulder, right_hip, right_knee)
            avg_back_angle = (left_back_angle + right_back_angle) / 2
            accuracy = calculate_accuracy_score(avg_back_angle, stage)

            left_hand_below_knee = left_wrist[1] > left_knee[1]
            right_hand_below_knee = right_wrist[1] > right_knee[1]
            
            if avg_back_angle < 70 and (left_hand_below_knee or right_hand_below_knee) and stage == "up":
                stage = "down"
            elif avg_back_angle > 160 and not left_hand_below_knee and not right_hand_below_knee and stage == "down":
                stage = "up"
                counter += 1
                score_list.append(accuracy)
                print(f"✅ {counter}회 완료 (정확도: {accuracy})")
            
            if key == 32:  # 스페이스바를 누르면 횟수 증가
                counter += 1
                score_list.append(100)
                print(f"스페이스바로 {counter}회 완료")    
                
                if counter >= 12:
                    set_score = int(sum(score_list) / len(score_list)) if score_list else 0  # 평균 점수 계산
                    print(f"🏁 세트 완료! 평균 점수: {set_score}")

                    # Firebase 점수 업데이트
                    update_workout_score(user_id, "deadlift", set_score)
                    update_workout_score(user_id, "total", set_score)

                    set_counter += 1  # 세트 수 증가
                    counter = 0  # 반복 횟수 초기화
                    score_list = []  # 점수 리스트 초기화

            
        except Exception as e:
            print(e)
            pass
        
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        cv2.putText(image, f'Count: {counter}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(image, f'Set: {set_counter}', (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)  # 세트 수 출력
        cv2.putText(image, f'Accuracy: {accuracy}', (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow('Deadlift Tracker', image)
        
        key = cv2.waitKey(10) & 0xFF
        if key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()