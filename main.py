import os
import requests

# Текст запроса
prompt = "Напиши одно короткое предложение о космосе."

# 1. Пробуем ваш Cloudflare (с вашими ключами)
account_id = os.getenv("CF_ACCOUNT_ID")
api_token = os.getenv("CF_API_TOKEN")

print("1. Пробуем Cloudflare...")
try:
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/deepseek-ai/deepseek-v4-flash-0731"
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    res = requests.post(url, headers=headers, json={"messages": [{"role": "user", "content": prompt}]}, timeout=10)
    res.raise_for_status()
    print("✅ Успех от Cloudflare:", res.json()["result"]["response"])
except Exception as e:
    print("❌ Cloudflare не сработал. Переключаемся на резервный сервер без ключей...")
    
    # 2. Резервный сервер (Pollinations) — работает без ключей!
    try:
        # Простой GET-запрос к бесплатному API
        res2 = requests.get(f"https://text.pollinations.ai/{prompt}", timeout=15)
        res2.raise_for_status()
        print("✅ Успех от резервного сервера:", res2.text)
    except Exception as e2:
        print("❌ Ошибка резервного сервера:", e2)