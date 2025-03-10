import cv2
import mediapipe as mp
import numpy as np

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# 각도 계산 함수
def findAngle(a, b, c, minVis=0.8):
    if a.visibility > minVis and b.visibility > minVis and c.visibility > minVis:
        bc = np.array([c.x - b.x, c.y - b.y, c.z - b.z])
        ba = np.array([a.x - b.x, a.y - b.y, a.z - b.z])
        angle = np.arccos(np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))) * (180 / np.pi)
        return 360 - angle if angle > 180 else angle
    return -1

# 다리 상태 판별 함수
def legState(angle):
    if angle < 0:
        return 0  # 감지 안 됨
    elif angle < 105:
        return 1  # 스쿼트 자세
    elif angle < 150:
        return 2  # 중간 상태
    else:
        return 3  # 직립 상태

# 스쿼트 감지 및 카운트 함수
def start_squat_tracking(user_id):
    cap = cv2.VideoCapture(0)

    while cap.read()[1] is None:
        print("Waiting for Video")

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        repCount = 0
        lastState = 9  # 초기 상태: 직립

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("카메라 오류!")
                break

            frame = cv2.resize(frame, (1024, 600))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame.flags.writeable = False

            # MediaPipe를 이용한 자세 감지
            lm = pose.process(frame).pose_landmarks
            if lm is None:
                print("화면 안으로 들어오세요!")
                cv2.imshow("Squat Rep Counter", frame)
                cv2.waitKey(1)
                continue

            frame.flags.writeable = True
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # 랜드마크 그리기
            mp_drawing.draw_landmarks(frame, lm, mp_pose.POSE_CONNECTIONS)

            lm_arr = lm.landmark
            rAngle = findAngle(lm_arr[24], lm_arr[26], lm_arr[28])  # 오른쪽 다리
            lAngle = findAngle(lm_arr[23], lm_arr[25], lm_arr[27])  # 왼쪽 다리

            rState = legState(rAngle)
            lState = legState(lAngle)
            state = rState * lState

            # 스쿼트 상태 판별
            if state == 0:
                print("다리 감지 안됨")
            elif state % 2 == 0 or rState != lState:
                print("자세를 조정하세요!")
            else:
                if state == 1 or state == 9:
                    if lastState != state:
                        lastState = state
                        if lastState == 1:
                            repCount += 1
                            print(f"스쿼트 성공! 총 개수: {repCount}")

            cv2.imshow("Squat Rep Counter", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    cap.release()
    cv2.destroyAllWindows()
