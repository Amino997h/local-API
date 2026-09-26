import requests
import json
import config

API_URL = f"http://127.0.0.1:{config.PORT}/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {config.API_KEY}",
    "Content-Type": "application/json"
}

PAYLOAD = {
    "model": "gpt-4o",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "من أنت؟ أجب في سطر واحد فقط."}
    ],
    "temperature": 0.7
}

def test_chat_completion():
    print(f"🚀 إرسال طلب تجريبي إلى {API_URL}...")
    try:
        response = requests.post(API_URL, headers=HEADERS, json=PAYLOAD, timeout=180)
        print(f"الحالة: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("\n✅ تم تلقي الرد بنجاح بنمط OpenAI:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("\nالرد النهائي:")
            print(data["choices"][0]["message"]["content"])
        else:
            print(f"❌ خطأ: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ فشل الإتصال بالسيرفر: {e}")

if __name__ == "__main__":
    test_chat_completion()
