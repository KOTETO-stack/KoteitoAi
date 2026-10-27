import os
import requests

account_id = os.getenv("CF_ACCOUNT_ID")
api_token = os.getenv("CF_API_TOKEN")
user_prompt = os.getenv("USER_PROMPT", "Напиши приветствие и сгенерируй картинку с котом-программистом")

headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

# --- 1. Генерация текста ---
text_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/deepseek-ai/deepseek-v4-flash-0731"
text_payload = {
    "messages": [
        {"role": "system", "content": "Ты — KoteitoAI, умный и креативный помощник."},
        {"role": "user", "content": user_prompt}
    ]
}

print("--- Запрос к текстовой модели ---")
try:
    res_text = requests.post(text_url, headers=headers, json=text_payload)
    res_text.raise_for_status()
    print("Ответ:", res_text.json()["result"]["response"])
except Exception as e:
    print(f"Ошибка текста: {e}")

# --- 2. Генерация картинки ---
image_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
img_payload = {"prompt": user_prompt}

print("\n--- Запрос к модели изображений ---")
try:
    res_img = requests.post(image_url, headers=headers, json=img_payload)
    res_img.raise_for_status()
    # Сохраняем картинку
    with open("generated_image.jpg", "wb") as f:
        f.write(res_img.content)
    print("Картинка сохранена в файл 'generated_image.jpg'")
except Exception as e:
    print(f"Ошибка картинки: {e}")