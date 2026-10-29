import requests
import time
import os
import sys
import base64
import random

# --- НАСТРОЙКИ ---
TG_TOKEN = os.getenv("TG_BOT_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
GH_PAT = os.getenv("GH_PAT")
GH_REPO = os.getenv("GH_REPO")

# Функция для получения списка бесплатных прокси
def get_proxies():
    print("🔍 Ищем бесплатные прокси в интернете...")
    proxies = []
    try:
        # Берем список с популярного бесплатного API
        res = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all", timeout=10)
        if res.status_code == 200:
            for line in res.text.strip().split('\n'):
                if line:
                    proxies.append(f"http://{line.strip()}")
    except Exception as e:
        print(f"Ошибка загрузки списка: {e}")
    return proxies

# Функция для поиска одного рабочего прокси, через который достучится Telegram
def find_working_proxy(proxies):
    random.shuffle(proxies)
    # Проверяем только первые 20 штук, чтобы не ждать вечность
    for proxy in proxies[:20]:
        try:
            test_url = f"https://api.telegram.org/bot{TG_TOKEN}/getMe"
            res = requests.get(test_url, proxies={"http": proxy, "https": proxy}, timeout=5)
            if res.status_code == 200:
                print(f"✅ Найден рабочий прокси: {proxy}")
                return {"http": proxy, "https": proxy}
        except:
            pass # Если не сработал, идем к следующему
    return None

if not TG_TOKEN or not CF_ACCOUNT_ID or not CF_API_TOKEN:
    print("❌ Ошибка: не заданы переменные окружения!")
    sys.exit(1)

# Отключаем вебхук (пробуем напрямую, без прокси, так как для отключения обычно не банят)
try:
    requests.get(f"https://api.telegram.org/bot{TG_TOKEN}/deleteWebhook", timeout=10)
except:
    pass

last_update_id = 0
start_time = time.time()

print("🤖 Бот запущен (Режим: Авто-Прокси)")

# Ищем первый прокси
current_proxies = get_proxies()
working_proxies = find_working_proxy(current_proxies)

while time.time() - start_time < (5 * 3600 + 50 * 60):
    try:
        # Если прокси сдох, ищем новый
        if not working_proxies:
            print("⚠️ Прокси потерян. Ищем новый...")
            current_proxies = get_proxies()
            working_proxies = find_working_proxy(current_proxies)
            if not working_proxies:
                print("❌ Не удалось найти рабочий прокси. Ждем 30 секунд...")
                time.sleep(30)
                continue

        url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates?offset={last_update_id}&timeout=30"
        res = requests.get(url, proxies=working_proxies, timeout=35).json()

        if res.get("result"):
            for update in res["result"]:
                last_update_id = update["update_id"] + 1
                
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"].lower()

                    # --- ВИДЕО ---
                    if "видео" in text or "video" in text:
                        prompt = update["message"]["text"].replace("видео", "").replace("video", "").strip()
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", proxies=working_proxies, 
                                      json={"chat_id": chat_id, "text": "🎬 Запускаю генерацию видео на GitHub (3-5 минут). Я пришлю его сюда!"})
                        
                        gh_url = f"https://api.github.com/repos/{GH_REPO}/actions/workflows/video_pipeline.yml/dispatches"
                        requests.post(gh_url, headers={
                            "Authorization": f"Bearer {GH_PAT}",
                            "Accept": "application/vnd.github.v3+json",
                            "User-Agent": "Telegram-Bot"
                        }, json={"ref": "main", "inputs": {"prompt": prompt, "chat_id": str(chat_id)}})

                    # --- КАРТИНКА ---
                    elif "нарисуй" in text or "картинк" in text:
                        prompt = update["message"]["text"].replace("нарисуй", "").replace("картинку", "").strip()
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", proxies=working_proxies, 
                                      json={"chat_id": chat_id, "text": "🎨 Рисую..."})
                        
                        # Запрос к Cloudflare идет НАПРЯМУЮ, так как Cloudflare не забанен
                        cf_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
                        img_res = requests.post(cf_url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"}, 
                                                json={"prompt": prompt + ", high quality, masterpiece"})
                        
                        if img_res.status_code == 200:
                            img_data = img_res.json()["result"]["image"]
                            img_bytes = base64.b64decode(img_data)
                            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", proxies=working_proxies, 
                                          data={"chat_id": chat_id}, files={"photo": ("image.jpg", img_bytes)})
                        else:
                            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", proxies=working_proxies, 
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
                            
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", proxies=working_proxies, 
                                      json={"chat_id": chat_id, "text": reply})
    except Exception as e:
        print(f"⚠️ Ошибка (возможно, прокси умер): {e}")
        working_proxies = None # Сбрасываем прокси, чтобы найти новый
        time.sleep(2)

print("Время работы истекло. Запускаем следующий процесс...")