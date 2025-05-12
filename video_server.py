# ✅ video_server.py (노트북에서 실행)
import cv2
import socket
import struct
import pickle
import mediapipe as mp
import numpy as np

HOST = '0.0.0.0'
PORT = 8485

# MediaPipe 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# 각도 계산 함수
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)

# 서버 설정
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
print("[SERVER] 연결 대기 중...")

conn, addr = server_socket.accept()
print("[SERVER] 연결 완료:", addr)

data = b""
payload_size = struct.calcsize(">L")

while True:
    # 프레임 수신
    while len(data) < payload_size:
        packet = conn.recv(4096)
        if not packet:
            break
        data += packet

    if not data:
        break

    packed_size = data[:payload_size]
    data = data[payload_size:]
    frame_size = struct.unpack(">L", packed_size)[0]

    while len(data) < frame_size:
        data += conn.recv(4096)

    frame_data = data[:frame_size]
    data = data[frame_size:]

    # 영상 디코딩
    frame = pickle.loads(frame_data)
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
    frame = cv2.flip(frame, 0) 

    # 자세 분석
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    feedback = "자세 인식 불가"

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark
        try:
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                   landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                     landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

            angle = calculate_angle(hip, knee, ankle)
            feedback = f"스쿼트 각도: {int(angle)}도"

            # 자세 피드백
            if angle < 70:
                feedback += " (너무 깊어요)"
            elif angle > 110:
                feedback += " (좀 더 내려가세요)"
            else:
                feedback += " (좋은 자세입니다!)"

            # 결과 출력
            cv2.putText(frame, feedback, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0), 2)
        except:
            feedback = "자세 인식 오류"

        # 랜드마크 표시
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    cv2.imshow('파이보 영상 분석', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # 향후 피드백 전송 (선택 사항)
    # msg = feedback.encode('utf-8')
    # conn.send(struct.pack('>I', len(msg)) + msg)

conn.close()
cv2.destroyAllWindows()
