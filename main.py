import os
import requests

# Токен будет браться из переменной окружения (безопасно)
HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

# Ваш запрос
prompt = "Привет! Напиши короткий текст о космосе."
output = query({
    "inputs": prompt,
    "parameters": {"max_new_tokens": 500}
})

# Печатаем ответ (структура ответа может быть списком словарей)
print(output[0]['generated_text'] if isinstance(output, list) else output)