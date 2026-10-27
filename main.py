import os
import requests

account_id = os.getenv("CF_ACCOUNT_ID")
api_token = os.getenv("CF_API_TOKEN")
user_prompt = os.getenv("USER_PROMPT", "Привет! Расскажи что-нибудь интересное.")

api_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

payload = {
    "model": "@cf/meta/llama-3.1-8b-instruct",
    "messages": [
        {"role": "system", "content": "Ты — KoteitoAI, умный и полезный помощник. Отвечай кратко и по делу."},
        {"role": "user", "content": user_prompt}
    ]
}

try:
    print("Отправляем запрос в Cloudflare...")
    response = requests.post(api_url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    print("\n--- Ответ ИИ ---")
    print(result["choices"][0]["message"]["content"])
except Exception as e:
    print(f"Ошибка: {e}")
    print("Сырой ответ (для отладки):", response.text if 'response' in locals() else "Нет ответа")