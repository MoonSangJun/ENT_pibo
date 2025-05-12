# # features/communication/send_mp3_to_pibo.py
# import socket
# import struct
# import os
# from gtts import gTTS

# def send_tts_mp3_to_pibo(text):
#     SERVER_IP = '192.168.0.2'  # 🧠 파이보 IP
#     PORT = 8685

#     # 1. gTTS로 mp3 파일 생성
#     tts = gTTS(text=text, lang='ko')
#     temp_filename = "temp_tts.mp3"
#     tts.save(temp_filename)

#     # 2. mp3 파일을 읽어서 전송
#     with open(temp_filename, 'rb') as f:
#         mp3_data = f.read()

#     file_size = len(mp3_data)

#     try:
#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         sock.connect((SERVER_IP, PORT))
#         print("[TTS 송신기] 파이보에 연결됨")

#         # 3. 먼저 파일 크기 전송
#         sock.sendall(struct.pack(">L", file_size))

#         # 4. 파일 데이터 전송
#         sock.sendall(mp3_data)

#         print("[TTS 송신 완료]")

#     except Exception as e:
#         print("[TTS 송신 에러]:", e)
#     finally:
#         sock.close()
#         os.remove(temp_filename)  # 임시파일 삭제



# features/communication/send_mp3_to_pibo.py
import socket
import struct
import os
import tempfile
import asyncio
import edge_tts

async def send_tts_mp3_to_pibo(text):
    SERVER_IP = '192.168.0.5'  # 🧠 파이보 IP
    PORT = 8685
    VOICE = "ko-KR-InJoonNeural"
    RATE = "+10%"  # 말 속도 조절 가능

    try:
        # 1. 임시 mp3 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            temp_path = tmp_file.name

        tts = edge_tts.Communicate(text, voice=VOICE, rate=RATE)
        await tts.save(temp_path)

        # 2. mp3 파일 읽기
        with open(temp_path, 'rb') as f:
            mp3_data = f.read()

        file_size = len(mp3_data)

        # 3. 파이보로 전송
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, PORT))
        print("[TTS 송신기] 파이보에 연결됨")

        sock.sendall(struct.pack(">L", file_size))
        sock.sendall(mp3_data)

        print("[TTS 송신 완료]")

    except Exception as e:
        print("[TTS 송신 에러]:", e)

    finally:
        sock.close()
        if os.path.exists(temp_path):
            os.remove(temp_path)

# 외부에서 사용할 함수 형태로 wrapping
def send_tts(text):
    asyncio.run(send_tts_mp3_to_pibo(text))
