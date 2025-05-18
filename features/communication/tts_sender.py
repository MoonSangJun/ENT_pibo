# tts_sender.py
import socket
import struct

TTS_PORT = 8585
PIBO_IP = '192.168.247.22'  # 파이보 IP

def send_feedback_signal_to_pibo(feedback_text):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((PIBO_IP, TTS_PORT))

        encoded = feedback_text.encode('utf-8')
        header = struct.pack(">I", len(encoded))
        client_socket.sendall(header + encoded)

        client_socket.close()
        print(f"[송신 완료] 피드백 텍스트 전송: {feedback_text}")
    except Exception as e:
        print(f"[에러 발생] TTS 텍스트 전송 실패: {e}")
