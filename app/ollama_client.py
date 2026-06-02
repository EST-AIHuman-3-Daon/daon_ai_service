import requests
from typing import List, Dict, Any


OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"


def chat_with_ollama(
    model: str,
    messages: List[Dict[str, Any]],
) -> str:
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

    try:
        response = requests.post(
            OLLAMA_CHAT_URL,
            json=payload,
            timeout=300,
        )

        response.raise_for_status()

        data = response.json()

        print("OLLAMA RAW RESPONSE:", data)

        if "message" not in data:
            raise RuntimeError(
                f"Invalid Ollama response: {data}"
            )

        return data["message"]["content"]

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama 서버에 연결할 수 없습니다. (11434)"
        )

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Ollama 응답 시간이 초과되었습니다."
        )

    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"Ollama HTTP 오류: {e}"
        )

    except Exception as e:
        raise RuntimeError(
            f"Ollama 호출 실패: {e}"
        )