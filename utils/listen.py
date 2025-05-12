# voice/listen.py
import speech_recognition as sr

def listen_to_question(timeout=5, phrase_time_limit=5):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("🎙️ [듣는 중] 조용히 해주세요...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = recognizer.recognize_google(audio, language="ko-KR")
            print(f"📝 [인식 결과] {text}")
            return text
        except sr.WaitTimeoutError:
            print("⏳ [시간초과] 아무 말도 안들림")
            return None
        except sr.UnknownValueError:
            print("❓ [오류] 음성을 이해 못함")
            return None
        except sr.RequestError as e:
            print(f"🚫 [에러] 요청 실패: {e}")
            return None
