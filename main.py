import os
import requests

HF_TOKEN = os.getenv("HF_TOKEN")
# Используем стабильный бесплатный API
API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

# 1. ЗДЕСЬ МЫ НАСТРАИВАЕМ ХАРАКТЕР МОДЕЛИ ПОД ВАС:
system_instruction = "Ты — KoteitoAI, умный и креативный помощник. Отвечай кратко, по делу, с легким юмором. Ты эксперт в IT и дизайне."

# 2. ВАШ ЗАПРОС:
user_prompt = "Привет! Как дела? Напиши 3 идеи для стартапа."

# Собираем всё вместе в один текст для модели
full_prompt = f"<|system|>\n{system_instruction}</s>\n<|user|>\n{user_prompt}</s>\n<|assistant|>\n"

output = query({
    "inputs": full_prompt,
    "parameters": {"max_new_tokens": 500, "return_full_text": False}
})

# Печатаем результат
if isinstance(output, list) and len(output) > 0:
    print(output[0]['generated_text'])
else:
    print("Ошибка от сервера:", output)