import gtts
import io
import pygame
import threading

# Pygame 초기화
pygame.mixer.init()

def speak_feedback(text):
    tts = gtts.gTTS(text=text, lang='ko')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)

    pygame.mixer.music.load(fp, "mp3")
    pygame.mixer.music.play()

def play_feedback(text):
    threading.Thread(target=speak_feedback, args=(text,), daemon=True).start()