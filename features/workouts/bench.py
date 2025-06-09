import cv2
import mediapipe as mp
import threading
from datetime import datetime
import speech_recognition as sr
from utils.pose_utils import calculate_2d_angle
from utils.firebase_utils import update_workout_score, get_user_difficulty, get_user_pibo_mode
from utils.video_overlay_utils import all_landmarks_visible, draw_info_overlay
from features.video.camera_receive import get_frame_from_pibo
from features.communication.tts_stt_mac import speak # Changed from speak_feedback to speak

stop_exercise = False

def monitor_for_stop():
    global stop_exercise
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("[음성 감지] '종료' 명령 대기 중...")

    while not stop_exercise:
        with mic as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.5) 
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                command = recognizer.recognize_google(audio, language="ko-KR")
                print(f"[음성 인식 결과] {command}")

                if "종료" in command:
                    print("[종료 감지] 운동 종료를 시작합니다.")
                    stop_exercise = True
                    break

            except sr.WaitTimeoutError:
                pass 
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"[음성 인식 오류] 서비스 문제: {e}")
            except Exception as e:
                print(f"[예외 발생] 음성 감지 중 오류: {e}")
                continue

def run_bench(user_id, difficulty):
    global stop_exercise
    stop_exercise = False

    threading.Thread(target=monitor_for_stop, daemon=True).start()

    pibo_mode = get_user_pibo_mode(user_id)
    firebase_difficulty = get_user_difficulty(user_id) 
    reps_per_set = {"easy": 8, "normal": 12, "hard": 15}.get(firebase_difficulty, 12)

    counter, set_counter = 0, 0
    total_reps, total_exp = 0, 0
    score_list = []
    stage = None
    min_down_angle = None # Added for consistency, though bench might use it differently
    last_score = None
    start_time = datetime.now()

    mp_pose_instance = mp.solutions.pose
    required_landmarks = [
        mp_pose_instance.PoseLandmark.LEFT_SHOULDER.value,
        mp_pose_instance.PoseLandmark.LEFT_ELBOW.value,
        mp_pose_instance.PoseLandmark.LEFT_WRIST.value,
        mp_pose_instance.PoseLandmark.RIGHT_SHOULDER.value,
        mp_pose_instance.PoseLandmark.RIGHT_ELBOW.value,
        mp_pose_instance.PoseLandmark.RIGHT_WRIST.value
    ]

    feedback_flags = {
        "greeted": False,
        "encouraged": False,
        "visibility_prompted": False,
        "ready_prompted": False
    }

    frame_generator = get_frame_from_pibo()

    with mp_pose_instance.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        for frame in frame_generator:
            if stop_exercise:
                print("[운동 강제 종료 감지]")
                speak("벤치프레스 운동을 종료합니다.")
                break

            frame = cv2.flip(frame, 1)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            if not feedback_flags["greeted"]:
                if pibo_mode == "friendly":
                    speak("벤치프레스 시작합니다. 이번 운동도 잘 해낼 거예요. 화이팅!")
                elif pibo_mode == "spartan":
                    speak("운동 시작이다. 자세 잡아라.")
                feedback_flags["greeted"] = True

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                visible = all_landmarks_visible(landmarks, required_landmarks)

                if not visible:
                    if not feedback_flags["visibility_prompted"]:
                        if pibo_mode == "friendly":
                            speak("몸 전체가 화면에 보이도록 누워 주세요.")
                        elif pibo_mode == "spartan":
                            speak("화면에 신체가 다 보이게 누워.")
                        feedback_flags["visibility_prompted"] = True
                        feedback_flags["ready_prompted"] = False
                else:
                    feedback_flags["visibility_prompted"] = False

                    if not feedback_flags["ready_prompted"]:
                        if pibo_mode == "friendly":
                            speak("좋아요, 준비됐어요! 벤치프레스를 시작하세요.")
                        elif pibo_mode == "spartan":
                            speak("자, 이제 벤치프레스 시작!")
                        feedback_flags["ready_prompted"] = True

                    try:
                        left_shoulder = [landmarks[mp_pose_instance.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose_instance.PoseLandmark.LEFT_SHOULDER.value].y]
                        left_elbow = [landmarks[mp_pose_instance.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose_instance.PoseLandmark.LEFT_ELBOW.value].y]
                        left_wrist = [landmarks[mp_pose_instance.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose_instance.PoseLandmark.LEFT_WRIST.value].y]

                        right_shoulder = [landmarks[mp_pose_instance.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose_instance.PoseLandmark.RIGHT_SHOULDER.value].y]
                        right_elbow = [landmarks[mp_pose_instance.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose_instance.PoseLandmark.RIGHT_ELBOW.value].y]
                        right_wrist = [landmarks[mp_pose_instance.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose_instance.PoseLandmark.RIGHT_WRIST.value].y]

                        left_angle = calculate_2d_angle(left_shoulder, left_elbow, left_wrist)
                        right_angle = calculate_2d_angle(right_shoulder, right_elbow, right_wrist)
                        avg_angle = (left_angle + right_angle) / 2
                        accuracy = max(0, 100 - abs(avg_angle - 160))
                        last_score = int(accuracy)

                        if avg_angle < 90:
                            if stage != "down":
                                stage = "down"
                                min_down_angle = avg_angle
                            else:
                                if avg_angle < min_down_angle:
                                    min_down_angle = avg_angle
                        
                        elif stage == "down" and avg_angle > 140:
                            stage = "up"
                            counter += 1
                            speak(f"{counter}회")
                            score_list.append(last_score)
                            total_reps += 1
                            total_exp += last_score

                            if min_down_angle is not None:
                                if min_down_angle > 80:
                                    if pibo_mode == "friendly":
                                        speak("가슴까지 더 내려주세요.")
                                    else:
                                        speak("더 내려. 가슴에 닿을 듯이.")
                                elif min_down_angle < 60:
                                    if pibo_mode == "friendly":
                                        speak("조금만 덜 내려주세요.")
                                    else:
                                        speak("너무 깊다. 컨트롤하며 내려.")
                                else:
                                    if pibo_mode == "friendly":
                                        speak("좋아요! 정확한 자세였어요.")
                                    else:
                                        speak("좋다. 이 정도면 합격이다.")
                                
                                min_down_angle = None # Reset for next rep

                            if counter >= int(reps_per_set * 0.7) and not feedback_flags["encouraged"]:
                                if pibo_mode == "friendly":
                                    speak("좋아요! 거의 다 왔어요. 조금만 더 힘내세요!")
                                else:
                                    speak("하나 더! 아직 멀었어!")
                                feedback_flags["encouraged"] = True

                            if counter >= reps_per_set:
                                avg_score = int(sum(score_list) / len(score_list)) if score_list else 0
                                if pibo_mode == "friendly":
                                    speak(f"세트 끝! 수고했어요~ 평균 점수는 {avg_score}점이에요.")
                                else:
                                    speak(f"세트 완료다. 점수는 {avg_score}점이다. 더 열심히 하도록!")
                                set_counter += 1
                                counter = 0
                                score_list = []
                                stage = None
                                feedback_flags["encouraged"] = False

                    except Exception as e:
                        print(f"[랜드마크 처리 오류] {e}")

                mp.solutions.drawing_utils.draw_landmarks(image, results.pose_landmarks, mp_pose_instance.POSE_CONNECTIONS)
                image = draw_info_overlay(image, counter, set_counter, last_score, visible) # Used 'visible' instead of 'ready'
            else:
                image = draw_info_overlay(image, counter, set_counter, last_score, False)

            cv2.imshow("Bench Tracker", image)

            key = cv2.waitKey(10) & 0xFF
            if key == ord(' '):
                counter += 1
                score_list.append(100)
                last_score = 100
                total_reps += 1
                total_exp += 100
                speak(f"{counter}회")

                if counter >= reps_per_set:
                    avg_score = int(sum(score_list) / len(score_list)) if score_list else 100
                    speak(f"세트 완료! 평균 점수는 {avg_score}점입니다.")
                    set_counter += 1
                    counter = 0
                    score_list = []
                    stage = None
                    feedback_flags["encouraged"] = False

            if stop_exercise or key == ord('q'): # Added stop_exercise check
                end_time = datetime.now()
                if total_reps > 0:
                    update_workout_score(user_id=user_id,
                                         workout_type="bench",
                                         score=total_exp,
                                         reps=total_reps,
                                         start_time=start_time,
                                         end_time=end_time)
                speak("운동을 종료합니다. 수고하셨습니다!")
                break

    # cap.release() # No longer needed with frame_generator
    cv2.destroyAllWindows()