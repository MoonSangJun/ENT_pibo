import cv2
import socket
import struct
import pickle

HOST = '0.0.0.0'
PORT = 8485

#소켓 통신
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
print("네트워크 연결 대기")

conn, addr = server_socket.accept()
print("연결 성공:", addr)
data = b""
payload_size = struct.calcsize(">L")

while True:
    # 필요한 만큼 데이터가 올 때까지 기다림
    while len(data) < payload_size:
        packet = conn.recv(4096)
        if not packet:
            break
        data += packet

    if not data:
        break

    packed_size = data[:payload_size]
    data = data[payload_size:]
    frame_size = struct.unpack(">L", packed_size)[0]

    while len(data) < frame_size:
        data += conn.recv(4096)

    frame_data = data[:frame_size]
    data = data[frame_size:]

    frame = pickle.loads(frame_data)
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

    frame = cv2.flip(frame, 0) 

    cv2.imshow('파이보 카메라 동작중', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

conn.close()
cv2.destroyAllWindows()
