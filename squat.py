import cv2
import mediapipe as mp
import numpy as np
from datetime import datetime
from firebase_config import db
from tts_stt import speak_feedback  # ✅ TTS (gTTS 등 사용)

# MediaPipe 초기화
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# ✅ 3D 각도 계산 함수
def calculate_3d_angle(a, b, c):
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)


# 정확도 점수 계산
def calculate_accuracy_score(squat_angle):
    ideal_angle = 90
    error = abs(squat_angle - ideal_angle)
    return int(max(0, 100 - error * 0.3))

# Firebase에 점수 저장
def update_workout_score(user_id, workout_type, score, date=None):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # 운동별 기록
    doc_ref = db.collection("users").document(user_id).collection(workout_type).document(date)
    doc = doc_ref.get()
    prev_score = doc.to_dict().get("score", 0) if doc.exists else 0
    prev_sets = doc.to_dict().get("sets", 0) if doc.exists else 0

    doc_ref.set({
        "score": prev_score + score,
        "sets": prev_sets + 1
    })

    # 날짜별 전체 저장
    total_ref = db.collection("users").document(user_id).collection("total").document(date)
    total_doc = total_ref.get()
    prev_total = total_doc.to_dict().get("score", 0) if total_doc.exists else 0
    total_ref.set({"score": prev_total + score})

    # 누적 경험치 저장
    exp_ref = db.collection("users").document(user_id).collection("total").document("exp")
    exp_doc = exp_ref.get()
    prev_exp = exp_doc.to_dict().get("score", 0) if exp_doc.exists else 0
    exp_ref.set({"score": prev_exp + score})

    # 레벨 업데이트
    update_user_exp_and_level(user_id, score)

def calculate_level(exp):
    level = 1
    threshold = 1000
    while exp >= threshold:
        level += 1
        threshold *= 2
    return level

def update_user_exp_and_level(user_id, added_score):
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    current_exp = user_doc.to_dict().get("exp", 0) if user_doc.exists else 0
    new_exp = current_exp + added_score
    new_level = calculate_level(new_exp)

    user_ref.set({
        "exp": new_exp,
        "level": new_level
    }, merge=True)

# ✅ 메인 스쿼트 함수
def run_squat(user_id):
    cap = cv2.VideoCapture(0)
    counter = 0
    stage = None
    score_list = []
    last_feedback = None
    min_squat_angle = None

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
                required_points = [mp_pose.PoseLandmark.LEFT_HIP.value,
                                   mp_pose.PoseLandmark.LEFT_KNEE.value,
                                   mp_pose.PoseLandmark.LEFT_ANKLE.value]
                if not all(landmarks[i].visibility > 0.5 for i in required_points):
                    continue

                # 좌표 추출 (3D)
                hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                       landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y,
                       landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].z]
                knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                        landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y,
                        landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].z]
                ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y,
                         landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].z]

                squat_angle = calculate_3d_angle(hip, knee, ankle)

                # down 진입
                if squat_angle < 120:
                    if stage != "down":
                        stage = "down"
                        min_squat_angle = squat_angle
                    else:
                        min_squat_angle = min(min_squat_angle, squat_angle)

                # up 전환
                elif squat_angle > 170 and stage == "down":
                    stage = "up"
                    counter += 1
                    score = calculate_accuracy_score(min_squat_angle)
                    score_list.append(score)
                    print(f"✅ {counter}회 완료 (최소 앵글: {min_squat_angle:.1f}, 정확도: {score})")

                    # 피드백
                    if min_squat_angle <= 75:
                        feedback = "조금만 덜 앉아도 괜찮아요."
                    elif min_squat_angle >= 90:
                        feedback = "조금 더 앉아주세요."
                    else:
                        feedback = "좋은 자세예요!"

                    if feedback != last_feedback:
                        speak_feedback(feedback)
                        last_feedback = feedback

                    min_squat_angle = None  # 초기화

                    # ✅ 세트마다 저장
                    if counter % 12 == 0:
                        set_score = int(sum(score_list) / len(score_list))
                        print(f"🏁 세트 완료! 평균 점수: {set_score}")
                        speak_feedback(f"세트 완료! 평균 점수는 {set_score}점입니다.")
                        update_workout_score(user_id, "squat", set_score)
                        score_list = []
                        counter = 0

                # 화면에 텍스트 표시
                cv2.putText(image, f'SQUAT ANGLE: {int(squat_angle)}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            except Exception:
                pass

            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            cv2.imshow("Squat Assistant", image)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()