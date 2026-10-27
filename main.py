import os
import requests
import urllib.parse
from gradio_client import Client, handle_file
import shutil

account_id = os.getenv("CF_ACCOUNT_ID")
api_token = os.getenv("CF_API_TOKEN")
user_prompt = os.getenv("USER_PROMPT", "Космический кот-программист")
headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

# --- 1. ГЕНЕРАЦИЯ ТЕКСТА (Cloudflare с фолбэком) ---
print("1. Генерируем текст...")
text_result = ""
# Список моделей на случай, если одна устареет или упадет
models_to_try = [
    "@cf/qwen/qwen3-30b-a3b-fp8",
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
]

for model in models_to_try:
    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Ты — KoteitoAI. Отвечай на русском языке, кратко и по делу."},
                {"role": "user", "content": user_prompt}
            ]
        }
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        res.raise_for_status()
        text_result = res.json()["choices"][0]["message"]["content"]
        print(f"✅ Текст получен через модель: {model}")
        break # Если получилось, выходим из цикла
    except Exception as e:
        print(f"⚠️ Модель {model} не сработала. Пробуем следующую...")

if not text_result:
    print("⚠️ Все модели Cloudflare упали. Переключаемся на резервный сервер...")
    try:
        safe_prompt = urllib.parse.quote(user_prompt + " (ответь на русском)")
        res = requests.get(f"https://text.pollinations.ai/{safe_prompt}", timeout=20)
        text_result = res.text
        print("✅ Текст получен с резервного сервера.")
    except Exception as e:
        print(f"❌ Ошибка текста: {e}")

with open("text.txt", "w", encoding="utf-8") as f:
    f.write(text_result)


# --- 2. ГЕНЕРАЦИЯ КАРТИНКИ (Cloudflare Flux) ---
print("\n2. Генерируем картинку...")
image_success = False
try:
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    payload = {"prompt": user_prompt + ", high quality, cinematic, 8k"}
    res = requests.post(url, headers=headers, json=payload, timeout=40)
    res.raise_for_status()
    with open("image.jpg", "wb") as f:
        f.write(res.content)
    print("✅ Картинка сгенерирована Cloudflare.")
    image_success = True
except Exception as e:
    print(f"⚠️ Cloudflare не смог сделать картинку. Пробуем резервный сервер...")
    try:
        safe_prompt = urllib.parse.quote(user_prompt)
        res = requests.get(f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true", timeout=40)
        res.raise_for_status()
        with open("image.jpg", "wb") as f:
            f.write(res.content)
        print("✅ Картинка сгенерирована резервным сервером.")
        image_success = True
    except Exception as e2:
        print(f"❌ Ошибка картинки: {e2}")


# --- 3. ГЕНЕРАЦИЯ ВИДЕО (Hugging Face) ---
print("\n3. Оживляем картинку (генерация видео)... Это займет 3-5 минут.")
if image_success:
    try:
        # Подключаемся к нейросети на Hugging Face
        client = Client("r3gm/wan2-2-fp8da-aoti-preview")
        result = client.predict(
            input_image=handle_file("image.jpg"),
            prompt=user_prompt + ", cinematic motion, 4k",
            api_name="/generate"
        )
        # Копируем полученный файл в наш проект
        shutil.copy(result, "video.mp4")
        print("✅ Видео готово!")
    except Exception as e:
        print(f"❌ Ошибка видео: {e}")
else:
    print("❌ Видео пропущено, так как не удалось создать картинку.")