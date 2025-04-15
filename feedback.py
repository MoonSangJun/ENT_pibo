# feedback.py
from tts_stt import speak_feedback

# 운동별 마지막 피드백 저장
_last_feedback = {}

def give_feedback(workout_type, angle):
    """
    workout_type: "squat", "bench", "deadlift" 중 하나
    angle: 운동에서 계산된 자세 각도
    """
    global _last_feedback

    if workout_type == "squat":
        if angle <= 75:
            feedback = "조금만 덜 앉아도 괜찮아요."
        elif angle >= 90:
            feedback = "조금 더 앉아주세요."
        else:
            feedback = "좋은 자세예요!"

    elif workout_type == "bench":
        if angle <= 50:
            feedback = "팔꿈치를 더 내려보세요."
        elif angle >= 80:
            feedback = "너무 높이 들고 있어요."
        else:
            feedback = "팔 동작이 좋습니다!"

    elif workout_type == "deadlift":
        if angle <= 70:
            feedback = "허리를 더 펴주세요."
        elif angle >= 100:
            feedback = "너무 숙였어요. 자세를 바로잡아야 해요."
        else:
            feedback = "좋은 자세입니다!"

    else:
        feedback = "운동 타입이 잘못되었습니다."

    # 이전 피드백과 다를 때만 출력
    if _last_feedback.get(workout_type) != feedback:
        speak_feedback(feedback)
        _last_feedback[workout_type] = feedback
