# # import cv2
# # import mediapipe as mp
# # import numpy as np
# # from datetime import datetime
# # from firebase_config import db
# # from tts_stt_mac import speak  # ✅ TTS (gTTS 등 사용)

# # # MediaPipe 초기화
# # mp_drawing = mp.solutions.drawing_utils
# # mp_pose = mp.solutions.pose

# # # ✅ 3D 각도 계산 함수
# # def calculate_3d_angle(a, b, c):
# #     ba = np.array(a) - np.array(b)
# #     bc = np.array(c) - np.array(b)
# #     cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
# #     angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
# #     return np.degrees(angle)


# # # 정확도 점수 계산
# # def calculate_accuracy_score(squat_angle):
# #     ideal_angle = 90
# #     error = abs(squat_angle - ideal_angle)
# #     return int(max(0, 100 - error * 0.3))

# # # Firebase에 점수 저장
# # def update_workout_score(user_id, workout_type, score, date=None):
# #     if date is None:
# #         date = datetime.now().strftime("%Y-%m-%d")

# #     # 운동별 기록
# #     doc_ref = db.collection("users").document(user_id).collection(workout_type).document(date)
# #     doc = doc_ref.get()
# #     prev_score = doc.to_dict().get("score", 0) if doc.exists else 0
# #     prev_sets = doc.to_dict().get("sets", 0) if doc.exists else 0

# #     doc_ref.set({
# #         "score": prev_score + score,
# #         "sets": prev_sets + 1
# #     })

# #     # 날짜별 전체 저장
# #     total_ref = db.collection("users").document(user_id).collection("total").document(date)
# #     total_doc = total_ref.get()
# #     prev_total = total_doc.to_dict().get("score", 0) if total_doc.exists else 0
# #     total_ref.set({"score": prev_total + score})

# #     # 누적 경험치 저장
# #     exp_ref = db.collection("users").document(user_id).collection("total").document("exp")
# #     exp_doc = exp_ref.get()
# #     prev_exp = exp_doc.to_dict().get("score", 0) if exp_doc.exists else 0
# #     exp_ref.set({"score": prev_exp + score})

# #     # 레벨 업데이트
# #     update_user_exp_and_level(user_id, score)

# # def calculate_level(exp):
# #     level = 1
# #     threshold = 1000
# #     while exp >= threshold:
# #         level += 1
# #         threshold *= 2
# #     return level

# # def update_user_exp_and_level(user_id, added_score):
# #     user_ref = db.collection("users").document(user_id)
# #     user_doc = user_ref.get()
# #     current_exp = user_doc.to_dict().get("exp", 0) if user_doc.exists else 0
# #     new_exp = current_exp + added_score
# #     new_level = calculate_level(new_exp)

# #     user_ref.set({
# #         "exp": new_exp,
# #         "level": new_level
# #     }, merge=True)

# # # ✅ 메인 스쿼트 함수
# # def run_squat(user_id):
# #     cap = cv2.VideoCapture(0)
# #     counter = 0
# #     stage = None
# #     score_list = []
# #     last_feedback = None
# #     min_squat_angle = None

# #     with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
# #         while cap.isOpened():
# #             ret, frame = cap.read()
# #             if not ret:
# #                 break

# #             image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
# #             image.flags.writeable = False
# #             results = pose.process(image)
# #             image.flags.writeable = True
# #             image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

# #             try:
# #                 if not results.pose_landmarks:
# #                     continue

# #                 landmarks = results.pose_landmarks.landmark
# #                 required_points = [mp_pose.PoseLandmark.LEFT_HIP.value,
# #                                    mp_pose.PoseLandmark.LEFT_KNEE.value,
# #                                    mp_pose.PoseLandmark.LEFT_ANKLE.value]
# #                 if not all(landmarks[i].visibility > 0.5 for i in required_points):
# #                     continue

# #                 # 좌표 추출 (3D)
# #                 hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
# #                        landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y,
# #                        landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].z]
# #                 knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
# #                         landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y,
# #                         landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].z]
# #                 ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
# #                          landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y,
# #                          landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].z]

# #                 squat_angle = calculate_3d_angle(hip, knee, ankle)

# #                 # down 진입
# #                 if squat_angle < 120:
# #                     if stage != "down":
# #                         stage = "down"
# #                         min_squat_angle = squat_angle
# #                     else:
# #                         min_squat_angle = min(min_squat_angle, squat_angle)

# #                 # up 전환
# #                 elif squat_angle > 170 and stage == "down":
# #                     stage = "up"
# #                     counter += 1
# #                     score = calculate_accuracy_score(min_squat_angle)
# #                     score_list.append(score)
# #                     print(f"✅ {counter}회 완료 (최소 앵글: {min_squat_angle:.1f}, 정확도: {score})")

# #                     # 피드백
# #                     if min_squat_angle <= 75:
# #                         feedback = "조금만 덜 앉아도 괜찮아요."
# #                     elif min_squat_angle >= 90:
# #                         feedback = "조금 더 앉아주세요."
# #                     else:
# #                         feedback = "좋은 자세예요!"

# #                     if feedback != last_feedback:
# #                         speak(feedback)
# #                         last_feedback = feedback

# #                     min_squat_angle = None  # 초기화

# #                     # ✅ 세트마다 저장
# #                     if counter % 12 == 0:
# #                         set_score = int(sum(score_list) / len(score_list))
# #                         print(f"🏁 세트 완료! 평균 점수: {set_score}")
# #                         speak(f"세트 완료! 평균 점수는 {set_score}점입니다.")
# #                         update_workout_score(user_id, "squat", set_score)
# #                         score_list = []
# #                         counter = 0

# #                 # 화면에 텍스트 표시
# #                 cv2.putText(image, f'SQUAT ANGLE: {int(squat_angle)}', (10, 30),
# #                             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

# #             except Exception:
# #                 pass

# #             mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
# #             cv2.imshow("Squat Assistant", image)
# #             if cv2.waitKey(10) & 0xFF == ord('q'):
# #                 break

# #     cap.release()
# #     cv2.destroyAllWindows()


# import cv2
# import mediapipe as mp
# import numpy as np
# from datetime import datetime
# from firebase_config import db
# from tts_stt_mac import speak  # 나중에 사용할 피드백 함수
# from camera_receive import get_frame_from_pibo
# from tts_sender import send_feedback_signal_to_pibo

# # MediaPipe 초기화
# mp_drawing = mp.solutions.drawing_utils
# mp_pose = mp.solutions.pose

# # 각도 계산 함수 (3D)
# def calculate_3d_angle(a, b, c):
#     ba = np.array(a) - np.array(b)
#     bc = np.array(c) - np.array(b)
#     cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
#     angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
#     return np.degrees(angle)

# # 정확도 점수 계산
# def calculate_accuracy_score(squat_angle):
#     ideal_angle = 90
#     error = abs(squat_angle - ideal_angle)
#     return int(max(0, 100 - error * 0.3))

# # Firebase 업데이트 함수들
# def update_workout_score(user_id, workout_type, score, date=None):
#     if date is None:
#         date = datetime.now().strftime("%Y-%m-%d")

#     doc_ref = db.collection("users").document(user_id).collection(workout_type).document(date)
#     doc = doc_ref.get()
#     prev_score = doc.to_dict().get("score", 0) if doc.exists else 0
#     prev_sets = doc.to_dict().get("sets", 0) if doc.exists else 0

#     doc_ref.set({
#         "score": prev_score + score,
#         "sets": prev_sets + 1
#     })

#     total_ref = db.collection("users").document(user_id).collection("total").document(date)
#     total_doc = total_ref.get()
#     prev_total = total_doc.to_dict().get("score", 0) if total_doc.exists else 0
#     total_ref.set({"score": prev_total + score})

#     exp_ref = db.collection("users").document(user_id).collection("total").document("exp")
#     exp_doc = exp_ref.get()
#     prev_exp = exp_doc.to_dict().get("score", 0) if exp_doc.exists else 0
#     exp_ref.set({"score": prev_exp + score})

#     update_user_exp_and_level(user_id, score)

# def calculate_level(exp):
#     level = 1
#     threshold = 1000
#     while exp >= threshold:
#         level += 1
#         threshold *= 2
#     return level

# def update_user_exp_and_level(user_id, added_score):
#     user_ref = db.collection("users").document(user_id)
#     user_doc = user_ref.get()
#     current_exp = user_doc.to_dict().get("exp", 0) if user_doc.exists else 0
#     new_exp = current_exp + added_score
#     new_level = calculate_level(new_exp)

#     user_ref.set({
#         "exp": new_exp,
#         "level": new_level
#     }, merge=True)

# # ✅ 스쿼트 실행 함수 (파이보 영상 수신 기반)
# def run_squat(user_id):
#     counter = 0
#     stage = None
#     score_list = []
#     last_feedback = None
#     min_squat_angle = None

#     frame_generator = get_frame_from_pibo()

#     with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
#         for frame in frame_generator:
#             if frame is None:
#                 print("[경고] 프레임이 None입니다.")
#                 continue

#             #print("[run_squat] 프레임 수신 완료")

#             try:
#                 image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                 image.flags.writeable = False
#                 results = pose.process(image)
#                 image.flags.writeable = True
#                 image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                
#                 if image is None:
#                     print("[오류] 변환된 이미지가 None입니다.")
#                     continue

#                 if results.pose_landmarks:
#                     landmarks = results.pose_landmarks.landmark
#                     required_points = [mp_pose.PoseLandmark.LEFT_HIP.value,
#                                        mp_pose.PoseLandmark.LEFT_KNEE.value,
#                                        mp_pose.PoseLandmark.LEFT_ANKLE.value]
#                     if not all(landmarks[i].visibility > 0.5 for i in required_points):
#                         continue

#                     hip = [landmarks[required_points[0]].x, landmarks[required_points[0]].y, landmarks[required_points[0]].z]
#                     knee = [landmarks[required_points[1]].x, landmarks[required_points[1]].y, landmarks[required_points[1]].z]
#                     ankle = [landmarks[required_points[2]].x, landmarks[required_points[2]].y, landmarks[required_points[2]].z]

#                     squat_angle = calculate_3d_angle(hip, knee, ankle)

#                     # down 상태
#                     if squat_angle < 120:
#                         if stage != "down":
#                             stage = "down"
#                             min_squat_angle = squat_angle
#                         else:
#                             min_squat_angle = min(min_squat_angle, squat_angle)

#                     # up 상태
#                     elif squat_angle > 170 and stage == "down":
#                         stage = "up"
#                         counter += 1
#                         score = calculate_accuracy_score(min_squat_angle)
#                         score_list.append(score)

#                         print(f"✅ {counter}회 완료 (최소 앵글: {min_squat_angle:.1f}, 정확도: {score})")

#                         feedback = "좋은 자세예요!"
#                         if min_squat_angle <= 75:
#                             feedback = "조금만 덜 앉아도 괜찮아요."
#                         elif min_squat_angle >= 90:
#                             feedback = "조금 더 앉아주세요."

#                         if feedback != last_feedback:
#                             send_feedback_signal_to_pibo(feedback)
#                             print("[피드백]", feedback)
#                             last_feedback = feedback

#                         min_squat_angle = None

#                         if counter % 12 == 0:
#                             set_score = int(sum(score_list) / len(score_list))
#                             print(f"\n🏁 세트 완료! 평균 점수: {set_score}")
#                             update_workout_score(user_id, "squat", set_score)
#                             score_list = []
#                             counter = 0

#                     cv2.putText(image, f'SQUAT ANGLE: {int(squat_angle)}', (10, 30),
#                                 cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

#                 else:
#                     print("[경고] 랜드마크 인식 실패")
                    
#                 mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
#                 # ✅ 항상 출력
#                 cv2.imshow("Squat Assistant", image)
#                 if cv2.waitKey(1) & 0xFF == ord('q'):
#                     print("[종료] 사용자 종료")
#                     break

#             except Exception as e:
#                 print("[예외 발생]", e)

#     cv2.destroyAllWindows()


import cv2
import threading
import mediapipe as mp
from utils.pose_utils import calculate_2d_angle
from utils.firebase_utils import update_workout_score
from utils.video_overlay_utils import all_landmarks_visible, draw_info_overlay
from features.video.camera_receive import get_frame_from_pibo
from features.communication.tts_sender import send_feedback_signal_to_pibo
from features.communication.tts_stt_mac import speak 
import speech_recognition as sr

from features.communication.send_mp3_pibo import send_tts_mp3_to_pibo

stop_exercise = False

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


def run_squat(user_id):
    global stop_exercise
    stop_exercise = False 

    threading.Thread(target=monitor_for_stop, daemon=True).start()

    counter, set_counter = 0, 0
    stage = None
    score_list = []
    last_score = None
    min_squat_angle = None
    last_feedback = None
    mp_pose_instance = mp.solutions.pose

    frame_generator = get_frame_from_pibo()

    required_landmarks = [23, 25, 27, 24, 26, 28]

    with mp_pose_instance.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        for frame in frame_generator:
            if stop_exercise:
                print("[운동 강제 종료 감지]")
                break
            #ret, frame = cap.read()
            # if not ret:
            #     break

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
                        hip = [landmarks[23].x, landmarks[23].y]
                        knee = [landmarks[25].x, landmarks[25].y]
                        ankle = [landmarks[27].x, landmarks[27].y]
                        angle = calculate_2d_angle(hip, knee, ankle)

                        if angle < 120:
                            if stage != "down":
                                stage = "down"
                                min_squat_angle = angle
                            else:
                                min_squat_angle = min(min_squat_angle, angle)
                        elif angle > 170 and stage == "down":
                            stage = "up"
                            counter += 1
                            score = max(0, 100 - abs(min_squat_angle - 90) * 0.3)
                            last_score = int(score)
                            score_list.append(last_score)

                            feedback = (
                                "조금만 덜 앉아도 괜찮아요." if min_squat_angle <= 75
                                else "조금 더 앉아주세요." if min_squat_angle >= 90
                                else "좋은 자세예요!"
                            )
                        

                            if feedback != last_feedback:
                                #send_feedback_signal_to_pibo(feedback)
                                send_tts_mp3_to_pibo(feedback)

                                #speak(feedback)
                                #굳이 파이보로 말할 필요가 있을까??
                                #노트북 으로 하는 버전, 파이보로 하는 버전 2개 하면 좋을듯
                                last_feedback = feedback

                            min_squat_angle = None

                            if counter >= 12:
                                avg_score = int(sum(score_list) / len(score_list))
                                #speak(f"세트 완료! 평균 점수는 {avg_score}점입니다.")
                                update_workout_score(user_id, "squat", avg_score, reps=12, sets=1)
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

            cv2.imshow("Squat Assistant", image)
            
            key = cv2.waitKey(10) & 0xFF
            if key == ord(' '):
                counter += 1
                score_list.append(100)
                last_score = 100

            # 추가
            if counter >= 12:
                avg_score = int(sum(score_list) / len(score_list)) if score_list else 100
                update_workout_score(user_id, "squat", avg_score)
                counter = 0
                score_list = []
                set_counter += 1            
            
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    
    cv2.destroyAllWindows()