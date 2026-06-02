import requests
from typing import List, Dict, Any


OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"


def chat_with_ollama(model: str, messages: List[Dict[str, Any]]) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.8,
            "repeat_penalty": 1.4,
            "num_predict": 128,
            "num_ctx": 2048,
        },
        "keep_alive": "10m",
    }

    response = requests.post(
        OLLAMA_CHAT_URL,
        json=payload,
        timeout=300,
    )
    response.raise_for_status()

    data = response.json()
    return data["message"]["content"]