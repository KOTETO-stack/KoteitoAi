import requests
import time
import os
import sys
import base64

# --- НАСТРОЙКИ ---
TG_TOKEN = os.getenv("TG_BOT_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
GH_PAT = os.getenv("GH_PAT")
GH_REPO = os.getenv("GH_REPO")

if not TG_TOKEN or not CF_ACCOUNT_ID or not CF_API_TOKEN:
    print("❌ Ошибка: не заданы переменные окружения!")
    sys.exit(1)

# Отключаем вебхук, чтобы Telegram разрешил нам забирать сообщения самим
requests.get(f"https://api.telegram.org/bot{TG_TOKEN}/deleteWebhook")

last_update_id = 0
start_time = time.time()

print("🤖 Бот запущен в режиме Long Polling (работает 5ч 50м)")

# Работаем 5 часов 50 минут (чтобы GitHub не убил процесс за 6 часов)
while time.time() - start_time < (5 * 3600 + 50 * 60):
    try:
        # Спрашиваем у Telegram новые сообщения (ждем до 30 секунд)
        url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates?offset={last_update_id}&timeout=30"
        res = requests.get(url, timeout=35).json()

        if res.get("result"):
            for update in res["result"]:
                last_update_id = update["update_id"] + 1
                
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"].lower()

                    # --- ВИДЕО ---
                    if "видео" in text or "video" in text:
                        prompt = update["message"]["text"].replace("видео", "").replace("video", "").strip()
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                                      json={"chat_id": chat_id, "text": "🎬 Запускаю генерацию видео на GitHub (3-5 минут). Я пришлю его сюда!"})
                        
                        # Отправляем команду на GitHub (запускаем video_pipeline.yml)
                        gh_url = f"https://api.github.com/repos/{GH_REPO}/actions/workflows/video_pipeline.yml/dispatches"
                        requests.post(gh_url, headers={
                            "Authorization": f"Bearer {GH_PAT}",
                            "Accept": "application/vnd.github.v3+json",
                            "User-Agent": "Telegram-Bot"
                        }, json={"ref": "main", "inputs": {"prompt": prompt, "chat_id": str(chat_id)}})

                    # --- КАРТИНКА ---
                    elif "нарисуй" in text or "картинк" in text:
                        prompt = update["message"]["text"].replace("нарисуй", "").replace("картинку", "").strip()
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                                      json={"chat_id": chat_id, "text": "🎨 Рисую..."})
                        
                        cf_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
                        img_res = requests.post(cf_url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"}, 
                                                json={"prompt": prompt + ", high quality, masterpiece"})
                        
                        if img_res.status_code == 200:
                            img_data = img_res.json()["result"]["image"]
                            img_bytes = base64.b64decode(img_data)
                            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                                          data={"chat_id": chat_id}, files={"photo": ("image.jpg", img_bytes)})
                        else:
                            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                                          json={"chat_id": chat_id, "text": f"❌ Ошибка картинки. Код: {img_res.status_code}"})
                    
                    # --- ТЕКСТ ---
                    else:
                        cf_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1/chat/completions"
                        text_res = requests.post(cf_url, headers={"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}, 
                                                 json={"model": "@cf/qwen/qwen3-30b-a3b-fp8", "messages": [{"role": "user", "content": update["message"]["text"]}]})
                        
                        if text_res.status_code == 200:
                            reply = text_res.json()["choices"][0]["message"]["content"]
                        else:
                            reply = "❌ Ошибка текстовой модели."
                            
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                                      json={"chat_id": chat_id, "text": reply})
    except Exception as e:
        print(f"Ошибка в цикле: {e}")
        time.sleep(5)

print("Время работы истекло. Запускаем следующий процесс...")