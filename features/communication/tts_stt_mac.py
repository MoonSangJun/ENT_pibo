# from gtts import gTTS
# import os
# import tempfile

# def speak(text, lang='ko'):
#     tts = gTTS(text=text, lang=lang)
#     with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
#         tts.save(fp.name)
#         os.system(f"afplay {fp.name}")  # Mac 기준
#         # Windows면 → os.system(f"start {fp.name}")

import asyncio
import edge_tts
import os
import tempfile
import platform

async def _edge_speak(text: str, lang: str = "ko-KR", voice: str = "ko-KR-InJoonNeural", rate: str = "+0%"):
    try:
        # 임시 mp3 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name

        communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
        await communicate.save(temp_path)

        # OS에 따라 재생 명령 분기
        if platform.system() == "Darwin":  # macOS
            os.system(f"afplay {temp_path}")
        elif platform.system() == "Windows":
            os.system(f"start {temp_path}")
        else:  # Linux
            os.system(f"mpg123 {temp_path}")

        os.remove(temp_path)

    except Exception as e:
        print(f"🚫 [TTS 오류]: {e}")

def speak(text, lang='ko'):
    asyncio.run(_edge_speak(text))
