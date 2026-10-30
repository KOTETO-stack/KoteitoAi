import os
import requests
import base64
from gradio_client import Client, handle_file

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_WORKER_URL = os.getenv("CF_WORKER_URL")
BOT_SECRET = os.getenv("BOT_SECRET")
CHAT_ID = os.getenv("CHAT_ID")
USER_PROMPT = os.getenv("USER_PROMPT")

headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
cf_base = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run"

def send_to_cf(msg_type, content, caption=""):
    requests.post(f"{CF_WORKER_URL}/send", json={
        "secret": BOT_SECRET, "chat_id": CHAT_ID, "type": msg_type, "content": content, "caption": caption
    })

# --- 1. Генерация текста (каскад моделей) ---
MODELS = [
    "@cf/moonshotai/kimi-k2.6",
    "@cf/qwen/qwen3.8-27b",
    "@cf/deepseek-ai/deepseek-v4-flash-0731",
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "@cf/zai-org/glm-4.7-flash",
    "@cf/qwen/qwen3-30b-a3b-fp8"
]

text_result = ""
for model in MODELS:
    try:
        res = requests.post(f"{cf_base}/{model}", headers=headers, json={
            "messages": [
                {"role": "system", "content": "Ты — KoteitoAI. Отвечай на русском языке."},
                {"role": "user", "content": USER_PROMPT}
            ]
        }, timeout=30)
        res.raise_for_status()
        text_result = res.json()["result"]["response"]
        break
    except Exception:
        continue

if text_result:
    send_to_cf("text", text_result)

# --- 2. Генерация изображения ---
image_success = False
img_base64 = ""
try:
    img_res = requests.post(f"{cf_base}/@cf/black-forest-labs/flux-1-schnell", headers=headers, 
                            json={"prompt": USER_PROMPT + ", masterpiece, best quality"}, timeout=40)
    img_res.raise_for_status()
    img_base64 = img_res.json()["result"]["image"]
    send_to_cf("photo", img_base64, f"🖼 {USER_PROMPT}")
    image_success = True
except Exception:
    pass

# --- 3. Генерация видео (если запрошено) ---
if image_success and any(w in USER_PROMPT.lower() for w in ["видео", "video"]):
    try:
        with open("temp.jpg", "wb") as f:
            f.write(base64.b64decode(img_base64))
        client = Client("r3gm/wan2-2-fp8da-aoti-preview")
        result = client.predict(input_image=handle_file("temp.jpg"), prompt=USER_PROMPT, api_name="/generate")
        with open(result, "rb") as v:
            send_to_cf("video", base64.b64encode(v.read()).decode('utf-8'), "🎬 Видео")
    except Exception:
        pass