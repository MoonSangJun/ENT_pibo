import socket
import struct

def send_motion_command(motion_name):
    HOST = '192.168.247.22'  # 예: 192.168.0.5
    PORT = 8787  # 모션 수신 전용 포트

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))

        data = motion_name.encode('utf-8')
        sock.sendall(struct.pack('>I', len(data)) + data)
        print(f"[명령 전송] {motion_name}")
    except Exception as e:
        print("[전송 실패]", e)
    finally:
        sock.close()
