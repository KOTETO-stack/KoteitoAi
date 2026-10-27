import os
import requests

HF_TOKEN = os.getenv("HF_TOKEN")
# Используем OpenAI-совместимый роутер Hugging Face
API_URL = "https://router.huggingface.co/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

prompt = "Привет! Напиши короткий текст о космосе."
payload = {
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 500
}

output = query(payload)
print(output["choices"][0]["message"]["content"])