import os
import requests
from gradio_client import Client, handle_file

account_id = os.getenv("CF_ACCOUNT_ID")
api_token = os.getenv("CF_API_TOKEN")
user_prompt = os.getenv("USER_PROMPT", "Кот-программист сидит за ноутбуком")

headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

# --- 1. Текст ---
print("1. Генерируем текст...")
text_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/deepseek-ai/deepseek-v4-flash-0731"
text_res = requests.post(text_url, headers=headers, json={"messages": [{"role": "user", "content": user_prompt}]})
try:
    print("Текст:", text_res.json()["result"]["response"])
except:
    print("Ошибка текста (пропускаем)")

# --- 2. Картинка ---
print("\n2. Генерируем картинку...")
img_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
img_res = requests.post(img_url, headers=headers, json={"prompt": user_prompt})
with open("image.jpg", "wb") as f:
    f.write(img_res.content)
print("Картинка сохранена в image.jpg")

# --- 3. Видео (Hugging Face) ---
print("\n3. Генерируем видео (это займет несколько минут)...")
try:
    # Подключаемся к бесплатному Space на HF
    client = Client("r3gm/wan2-2-fp8da-aoti-preview")
    
    # Отправляем нашу картинку и промпт (на английском)
    result = client.predict(
        input_image=handle_file("image.jpg"),
        prompt=user_prompt + ", cinematic, high quality",
        api_name="/generate" # обычно так называется функция генерации
    )
    
    # Сохраняем видео
    import shutil
    shutil.copy(result, "video.mp4")
    print("Видео успешно сохранено в video.mp4")
except Exception as e:
    print(f"Ошибка видео: {e}")