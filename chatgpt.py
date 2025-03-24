# 여기 아래는 chat GPT API 사용.. 일단은 유료버전인 것 같음.. 낫 이지한듯함


import openai
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
OPENAI_API_KEY = os.getenv("")

# OpenAI 클라이언트 초기화 (v1.0.0 이상)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ChatGPT API 호출 함수 (새로운 방식)
def ask_chatgpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 최신 모델 사용 가능
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"오류 발생: {e}"

# 터미널 기반 대화 함수
def chat_with_gpt():
    print("\n🤖 Pibo Chat 시작! ('종료'라고 입력하면 끝낼 수 있어)\n")
    
    while True:
        user_input = input("💬 사용자: ")

        if user_input.lower() in ["종료", "exit", "quit"]:
            print("👋 대화를 종료합니다.")
            break

        response = ask_chatgpt(user_input)
        print(f"🤖 Pibo: {response}\n")

if __name__ == "__main__":
    chat_with_gpt()
