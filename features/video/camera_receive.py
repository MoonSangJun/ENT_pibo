import socket
import struct
import pickle
import cv2

HOST = '0.0.0.0'  # 모든 IP로부터 수신
PORT = 8485       # 파이보와 일치하는 포트

#서버 소켓 초기화
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
print("[서버 대기 중] 파이보 연결 기다리는 중...")

conn, addr = server_socket.accept()
print(f"[연결됨] 파이보 주소: {addr}")


data = b"" 
payload_size = struct.calcsize(">L")


def get_frame_from_pibo():
    global data
    frame_count = 0  # 몇 번째 프레임인지 확인

    while True:
        try:
            # [1] 패킷 수신 시작
            while len(data) < payload_size:
                packet = conn.recv(4096)
                if not packet:
                    print("[수신 실패] 초기 패킷 없음")
                    continue
                data += packet
            #print("[1] 프레임 헤더 수신 완료")

            # [2] 프레임 크기 확인
            packed_size = data[:payload_size]
            data = data[payload_size:]
            frame_size = struct.unpack(">L", packed_size)[0]
            #print(f"[2] 프레임 크기: {frame_size}")

            # [3] 프레임 데이터 수신
            while len(data) < frame_size:
                packet = conn.recv(4096)
                if not packet:
                    print("[수신 실패] 프레임 데이터 없음")
                    continue
                data += packet
            #print("[3] 프레임 바이트 수신 완료")

            # [4] 데이터 디코딩
            frame_data = data[:frame_size]
            data = data[frame_size:]

            frame = pickle.loads(frame_data)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            frame = cv2.flip(frame, 0) 

            if frame is not None:
                frame_count += 1
                #print(f"[4] ✅ 프레임 {frame_count} 수신 및 디코딩 성공")
                yield frame
            else:
                #print("[4] ❌ 디코딩된 프레임이 None입니다")
                continue

        except Exception as e:
            print("[예외 발생]", e)
            continue
