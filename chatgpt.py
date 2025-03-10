#####챗 지피티 API가 유로라서 무료로 도전해볼려고 했으나.. 실패하였음.. 쉽지 않은것 같음 이슈


import g4f

def ask_gpt4free(prompt):
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4",
            provider=g4f.Provider.FreeChatgpt,
            messages=[{"role": "user", "content": prompt}]
        )

        if isinstance(response, list):
            return "".join([chunk.get("content", "") for chunk in response])
        return response

    except Exception as e:
        return f"오류 발생: {e}"

def chat_with_gpt():
    print("\n🤖 Pibo Chat 시작! ('종료'라고 입력하면 끝낼 수 있어)\n")

    while True:
        user_input = input("사용자: ")

        if user_input.lower() in ["종료", "exit", "quit"]:
            print("대화를 종료합니다.")
            break

        response = ask_gpt4free(user_input)
        print(f"Pibo: {response}\n")

if __name__ == "__main__":
    chat_with_gpt()
