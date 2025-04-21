from gtts import gTTS
import os
import tempfile

def speak_feedback(text, lang='ko'):
    tts = gTTS(text=text, lang=lang)
    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
        tts.save(fp.name)
        os.system(f"afplay {fp.name}")  # Mac 기준
        # Windows면 → os.system(f"start {fp.name}")