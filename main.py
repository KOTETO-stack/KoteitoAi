import os
import requests
import urllib.parse
from gradio_client import Client, handle_file

account_id = os.getenv("CF_ACCOUNT_ID")
api_token = os.getenv("CF_API_TOKEN")
user_prompt = os.getenv("USER_PROMPT", "Кот-программист сидит за ноутбуком")
headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

# --- 1. ТЕКСТ (Cloudflare -> Pollinations) ---
print("1. Генерируем текст...")
text_result = ""
try:
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/deepseek-ai/deepseek-v4-flash-0731"
    res = requests.post(url, headers=headers, json={"messages": [{"role": "user", "content": user_prompt}]}, timeout=15)
    res.raise_for_status()
    text_result = res.json()["result"]["response"]
    print("✅ Текст от Cloudflare")
except Exception as e:
    print(f"⚠️ Cloudflare текст не сработал ({e}). Переключаемся...")
    try:
        safe_prompt = urllib.parse.quote(user_prompt)
        res = requests.get(f"https://text.pollinations.ai/{safe_prompt}", timeout=15)
        text_result = res.text
        print("✅ Текст от Pollinations (резерв)")
    except Exception as e2:
        print(f"❌ Ошибка текста: {e2}")

with open("text.txt", "w", encoding="utf-8") as f:
    f.write(text_result)


# --- 2. КАРТИНКА (Cloudflare -> Pollinations Image) ---
print("\n2. Генерируем картинку...")
image_success = False
try:
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    res = requests.post(url, headers=headers, json={"prompt": user_prompt}, timeout=30)
    res.raise_for_status()
    with open("image.jpg", "wb") as f:
        f.write(res.content)
    print("✅ Картинка от Cloudflare")
    image_success = True
except Exception as e:
    print(f"⚠️ Cloudflare картинка не сработала ({e}). Переключаемся...")
    try:
        safe_prompt = urllib.parse.quote(user_prompt)
        res = requests.get(f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true", timeout=30)
        res.raise_for_status()
        with open("image.jpg", "wb") as f:
            f.write(res.content)
        print("✅ Картинка от Pollinations (резерв)")
        image_success = True
    except Exception as e2:
        print(f"❌ Ошибка картинки: {e2}")


# --- 3. ВИДЕО (Hugging Face) ---
print("\n3. Генерируем видео (займет пару минут)...")
if image_success:
    try:
        client = Client("r3gm/wan2-2-fp8da-aoti-preview")
        result = client.predict(
            input_image=handle_file("image.jpg"),
            prompt=user_prompt + ", cinematic, 4k",
            api_name="/generate"
        )
        import shutil
        shutil.copy(result, "video.mp4")
        print("✅ Видео готово!")
    except Exception as e:
        print(f"❌ Ошибка видео: {e}")
else:
    print("❌ Видео пропущено, так как картинка не сгенерировалась.")