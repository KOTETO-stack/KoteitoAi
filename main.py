import os
import requests
import base64
from huggingface_hub import InferenceClient

cf_account_id = os.getenv("CF_ACCOUNT_ID")
cf_api_token = os.getenv("CF_API_TOKEN")
tg_token = os.getenv("TG_BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")
hf_token = os.getenv("HF_TOKEN")
prompt = os.getenv("USER_PROMPT", "A cat")

cf_headers = {"Authorization": f"Bearer {cf_api_token}"}

# 1. КАРТИНКА (Cloudflare Flux)
print("Генерация картинки...")
img_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
img_res = requests.post(img_url, headers=cf_headers, json={"prompt": prompt + ", masterpiece, high quality"})
with open("image.jpg", "wb") as f:
    f.write(img_res.content)

# 2. ВИДЕО (Hugging Face Hub)
print("Генерация видео (это займет время)...")
try:
    client = InferenceClient(token=hf_token)
    # Используем стабильную модель text-to-video
    video = client.text_to_video(prompt, model="Wan-AI/Wan2.2-T2V-A14B")
    video.save("video.mp4")
    print("Видео готово!")
except Exception as e:
    print(f"Ошибка видео: {e}")

# 3. ОТПРАВКА
if chat_id and tg_token:
    with open("image.jpg", "rb") as photo:
        requests.post(f"https://api.telegram.org/bot{tg_token}/sendPhoto", data={"chat_id": chat_id, "caption": "🖼 Картинка"}, files={"photo": photo})
    
    if os.path.exists("video.mp4"):
        with open("video.mp4", "rb") as video:
            requests.post(f"https://api.telegram.org/bot{tg_token}/sendVideo", data={"chat_id": chat_id, "caption": "🎬 Видео"}, files={"video": video})