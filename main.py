import os
import requests
import urllib.parse
from gradio_client import Client, handle_file
import shutil

# --- НАСТРОЙКИ ---
cf_account_id = os.getenv("CF_ACCOUNT_ID")
cf_api_token = os.getenv("CF_API_TOKEN")
gh_token = os.getenv("GH_MODELS_TOKEN")
user_prompt = os.getenv("USER_PROMPT", "Космический кот-программист")

cf_headers = {"Authorization": f"Bearer {cf_api_token}", "Content-Type": "application/json"}

# --- 1. ГЕНЕРАЦИЯ ТЕКСТА (GitHub Models -> Cloudflare -> Резерв) ---
print("1. Генерируем умный текст...")
text_result = ""

# Пробуем GitHub Models (GPT-4o-mini)
try:
    print("Пробуем GitHub Models (GPT-4o-mini)...")
    gh_url = "https://models.github.ai/inference/chat/completions"
    gh_payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Ты — KoteitoAI. Отвечай на русском языке, кратко и по делу."},
            {"role": "user", "content": user_prompt}
        ]
    }
    res = requests.post(gh_url, headers={"Authorization": f"Bearer {gh_token}", "Content-Type": "application/json"}, json=gh_payload, timeout=30)
    res.raise_for_status()
    text_result = res.json()["choices"][0]["message"]["content"]
    print("✅ Текст получен от GitHub Models!")
except Exception as e:
    print(f"⚠️ GitHub Models не сработал ({e}). Переключаемся на Cloudflare...")
    # Пробуем Cloudflare (Qwen)
    try:
        cf_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/v1/chat/completions"
        cf_payload = {
            "model": "@cf/qwen/qwen3-30b-a3b-fp8",
            "messages": [{"role": "user", "content": user_prompt}]
        }
        res = requests.post(cf_url, headers=cf_headers, json=cf_payload, timeout=20)
        res.raise_for_status()
        text_result = res.json()["choices"][0]["message"]["content"]
        print("✅ Текст получен от Cloudflare.")
    except Exception as e2:
        print(f"❌ Все текстовые модели упали. Ошибка: {e2}")

with open("text.txt", "w", encoding="utf-8") as f:
    f.write(text_result)

# --- 2. ГЕНЕРАЦИЯ КАРТИНКИ (Cloudflare Flux) ---
print("\n2. Генерируем картинку...")
image_success = False
try:
    img_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    img_payload = {"prompt": user_prompt + ", high quality, detailed"}
    res = requests.post(img_url, headers=cf_headers, json=img_payload, timeout=40)
    res.raise_for_status()
    with open("image.jpg", "wb") as f:
        f.write(res.content)
    print("✅ Картинка от Cloudflare!")
    image_success = True
except Exception as e:
    print(f"❌ Ошибка картинки: {e}")

# --- 3. ГЕНЕРАЦИЯ ВИДЕО (Hugging Face) ---
print("\n3. Оживляем картинку (генерация видео)... Это займет 3-5 минут.")
if image_success:
    try:
        client = Client("r3gm/wan2-2-fp8da-aoti-preview")
        result = client.predict(
            input_image=handle_file("image.jpg"),
            prompt=user_prompt + ", cinematic motion, 4k",
            api_name="/generate"
        )
        shutil.copy(result, "video.mp4")
        print("✅ Видео готово!")
    except Exception as e:
        print(f"❌ Ошибка видео: {e}")
else:
    print("❌ Видео пропущено (нет исходной картинки).")