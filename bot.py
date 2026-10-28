import requests
import time
import os
import sys

# --- НАСТРОЙКИ ---
TG_TOKEN = os.getenv("TG_BOT_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")

if not TG_TOKEN or not CF_ACCOUNT_ID or not CF_API_TOKEN:
    print("❌ Ошибка: не заданы переменные окружения!")
    sys.exit(1)

# Отключаем Webhook, чтобы Telegram разрешил нам забирать сообщения самим (Polling)
requests.get(f"https://api.telegram.org/bot{TG_TOKEN}/deleteWebhook")

last_update_id = 0
start_time = time.time()

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

                    # --- КАРТИНКА ---
                    if "нарисуй" in text or "картинк" in text:
                        prompt = update["message"]["text"].replace("нарисуй", "").replace("картинку", "").strip()
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                                      json={"chat_id": chat_id, "text": "🎨 Рисую..."})
                        
                        # Стучимся в Cloudflare
                        cf_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
                        img_res = requests.post(cf_url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"}, 
                                                json={"prompt": prompt + ", high quality"})
                        
                        if img_res.status_code == 200:
                            # Сохраняем и отправляем картинку (в реальности тут нужно декодировать base64)
                            import base64
                            img_data = img_res.json()["result"]["image"]
                            with open("temp_img.jpg", "wb") as f:
                                f.write(base64.b64decode(img_data))
                            
                            with open("temp_img.jpg", "rb") as photo:
                                requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                                              data={"chat_id": chat_id}, files={"photo": photo})
                        else:
                            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                                          json={"chat_id": chat_id, "text": "❌ Ошибка Cloudflare (лимит или токен)."})
                    
                    # --- ТЕКСТ (Эхо для примера, сюда можно вставить вызов нейросети) ---
                    else:
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                                      json={"chat_id": chat_id, "text": f"Ты написал: {text}"})
    except Exception as e:
        print(f"Ошибка в цикле: {e}")
        time.sleep(5) # Пауза при ошибке

print("Время работы истекло. Запускаем следующий процесс...")