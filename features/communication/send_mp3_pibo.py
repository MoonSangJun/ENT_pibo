# features/communication/send_mp3_to_pibo.py
import socket
import struct
import os
from gtts import gTTS

def send_tts_mp3_to_pibo(text):
    SERVER_IP = '192.168.0.5'  # 🧠 파이보 IP
    PORT = 8685

    # 1. gTTS로 mp3 파일 생성
    tts = gTTS(text=text, lang='ko')
    temp_filename = "temp_tts.mp3"
    tts.save(temp_filename)

    # 2. mp3 파일을 읽어서 전송
    with open(temp_filename, 'rb') as f:
        mp3_data = f.read()

    file_size = len(mp3_data)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, PORT))
        print("[TTS 송신기] 파이보에 연결됨")

        # 3. 먼저 파일 크기 전송
        sock.sendall(struct.pack(">L", file_size))

        # 4. 파일 데이터 전송
        sock.sendall(mp3_data)

        print("[TTS 송신 완료]")

    except Exception as e:
        print("[TTS 송신 에러]:", e)
    finally:
        sock.close()
        os.remove(temp_filename)  # 임시파일 삭제
