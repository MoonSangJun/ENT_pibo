from PIL import ImageFont, ImageDraw, Image
import numpy as np
import cv2

def all_landmarks_visible(landmarks, indices):
    return all(landmarks[i].visibility > 0.5 for i in indices)

def draw_info_overlay(image, counter, set_counter, last_score, ready):
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)

    # MacOS 시스템 기본 한글 폰트
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/AppleGothic.ttf", 32)

    status_text = "운동을 시작하세요" if ready else "화면에 맞춰 서주세요"
    draw.text((30, 30), f"반복 횟수: {counter}", font=font, fill=(0,255,0))
    draw.text((30, 70), f"세트 수: {set_counter}", font=font, fill=(0,255,0))
    draw.text((30, 110), f"이전 정확도: {last_score if last_score is not None else '-'}", font=font, fill=(0,255,0))
    draw.text((30, 150), status_text, font=font, fill=(0,0,255) if not ready else (255,255,0))

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)