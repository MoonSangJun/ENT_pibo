import cv2
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_config import db  # db는 초기화되어 있다고 가정

from features.video.camera_receive import get_frame_from_pibo
import cv2

# ✅ 파이보 카메라로 QR코드 읽기
def read_qr_from_pibo_camera():
    detector = cv2.QRCodeDetector()
    frame_generator = get_frame_from_pibo()

    print("파이보 카메라 활성화. QR 코드를 인식시켜주세요.")

    for frame in frame_generator:
        if frame is None:
            print("[경고] 프레임 수신 실패")
            continue

        data, bbox, _ = detector.detectAndDecode(frame)
        if data:
            print(f"✅ QR 코드 인식 완료! UID: {data}")
            cv2.destroyAllWindows()
            return data

        cv2.imshow('QR 코드 스캔 중 (q를 눌러 종료)', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("q를 눌러 종료했습니다.")
            break

    cv2.destroyAllWindows()
    return None


# QR 코드로 로그인하는 함수
def login_with_qr():
    uid = read_qr_from_pibo_camera()
    if uid is None:
        print("QR 코드를 인식하지 못했습니다.")
        return None

    try:
        user_ref = db.collection("users").document(uid)
        doc = user_ref.get()

        if doc.exists:
            user_data = doc.to_dict()
            print(f"\n로그인 성공! {user_data.get('name', '알 수 없음')}님 환영합니다!")
            print("\n어떤 운동을 하시겠습니까?")
            return uid
        else:
            print("로그인 실패! 해당 UID를 가진 유저가 존재하지 않습니다.")
            return None
    except Exception as e:
        print(f"로그인 중 오류 발생: {e}")
        return None
