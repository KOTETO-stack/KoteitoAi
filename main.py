import os
import requests
import urllib.parse
from gradio_client import Client, handle_file
import shutil

# --- НАСТРОЙКИ ---
cf_account_id = os.getenv("CF_ACCOUNT_ID")
cf_api_token = os.getenv("CF_API_TOKEN")
gh_token = os.getenv("GH_MODELS_TOKEN")
tg_token = os.getenv("TG_BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")
user_prompt = os.getenv("USER_PROMPT", "A beautiful landscape")

cf_headers = {"Authorization": f"Bearer {cf_api_token}", "Content-Type": "application/json"}

print(f"Запрос: {user_prompt}")
print(f"Chat ID: {chat_id}")

# --- 1. ТЕКСТ (GitHub Models -> Cloudflare Qwen) ---
text_result = ""
try:
    print("1. Генерация текста (GitHub Models)...")
    # Исправленный URL для GitHub Models
    gh_url = "https://models.inference.ai.azure.com/chat/completions"
    res = requests.post(
        gh_url, 
        headers={"Authorization": f"Bearer {gh_token}", "Content-Type": "application/json"}, 
        json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": user_prompt}]}, 
        timeout=30
    )
    res.raise_for_status()
    text_result = res.json()["choices"][0]["message"]["content"]
    print("✅ Текст получен от GitHub Models.")
except Exception as e:
    print(f"⚠️ GitHub Models не сработал ({e}). Пробуем Cloudflare Qwen...")
    try:
        cf_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/v1/chat/completions"
        res = requests.post(
            cf_url, 
            headers=cf_headers, 
            json={"model": "@cf/qwen/qwen3-30b-a3b-fp8", "messages": [{"role": "user", "content": user_prompt}]}, 
            timeout=20
        )
        res.raise_for_status()
        text_result = res.json()["choices"][0]["message"]["content"]
        print("✅ Текст получен от Cloudflare.")
    except Exception as e2:
        text_result = f"Ошибка текста: {e2}"
        print(f"❌ Все текстовые модели упали: {e2}")

with open("text.txt", "w", encoding="utf-8") as f:
    f.write(text_result)

# --- 2. КАРТИНКА (Cloudflare Flux) ---
print("\n2. Генерация картинки (Cloudflare Flux)...")
image_success = False
try:
    img_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    res = requests.post(
        img_url, 
        headers=cf_headers, 
        json={"prompt": user_prompt + ", masterpiece, highly detailed"}, 
        timeout=40
    )
    res.raise_for_status()
    with open("image.jpg", "wb") as f:
        f.write(res.content)
    image_success = True
    print("✅ Картинка готова.")
except Exception as e:
    print(f"❌ Ошибка картинки: {e}")

# --- 3. ВИДЕО (Hugging Face) ---
print("\n3. Генерация видео (Hugging Face)... Это займет 3-5 минут.")
video_success = False
if image_success:
    try:
        # Подключаемся к нейросети на Hugging Face
        client = Client("r3gm/wan2-2-fp8da-aoti-preview")
        result = client.predict(
            input_image=handle_file("image.jpg"),
            prompt=user_prompt + ", cinematic motion",
            api_name="/generate"
        )
        shutil.copy(result, "video.mp4")
        video_success = True
        print("✅ Видео готово.")
    except Exception as e:
        print(f"❌ Ошибка видео: {e}")
else:
    print("❌ Видео пропущено (нет исходной картинки).")

# --- 4. ОТПРАВКА В TELEGRAM ---
print("\n4. Отправка результатов в Telegram...")
if chat_id and tg_token:
    # Отправляем текст
    try:
        requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", 
            json={"chat_id": chat_id, "text": f"📝 Текст:\n{text_result[:4000]}"})
    except Exception as e:
        print(f"Ошибка отправки текста: {e}")

    # Отправляем картинку
    if image_success:
        try:
            with open("image.jpg", "rb") as photo:
                requests.post(f"https://api.telegram.org/bot{tg_token}/sendPhoto", 
                    data={"chat_id": chat_id, "caption": "🖼 Картинка готова"}, files={"photo": photo})
        except Exception as e:
            print(f"Ошибка отправки фото: {e}")

    # Отправляем видео
    if video_success:
        try:
            with open("video.mp4", "rb") as video:
                requests.post(f"https://api.telegram.org/bot{tg_token}/sendVideo", 
                    data={"chat_id": chat_id, "caption": "🎬 Видео готово!"}, files={"video": video})
        except Exception as e:
            print(f"Ошибка отправки видео: {e}")
else:
    print("⚠️ Не отправлено в Telegram: отсутствует Chat ID или TG_BOT_TOKEN.")

print("\nПроцесс завершен!")