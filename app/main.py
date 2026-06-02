from fastapi import FastAPI
from typing import List
from pydantic import BaseModel, Field
import json

from app.rag import build_vector_db, get_relevant_context
from app.ollama_client import chat_with_ollama

app = FastAPI()

MODEL_MAP = {
    # LoRA 모델 만들기 전 임시 모델
    # "friendly": "qwen2.5:7b",
    # "pressure": "qwen2.5:7b",

    # LoRA 모델 적용 후에는 아래처럼 교체
    "friendly": "ict-friendly",
    "pressure": "ict-pressure",
}

MAX_CONTEXT_LENGTH = 2000


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    persona: str = "friendly"
    question: str
    history: List[ChatMessage] = Field(default_factory=list)


@app.post("/rag/build")
def build_rag():
    build_vector_db()
    return {"message": "vector db created"}


@app.post("/chat")
def chat(req: ChatRequest):
    model = MODEL_MAP.get(req.persona, MODEL_MAP["friendly"])

    context = get_relevant_context(req.question)

    if not context:
        context = "관련 문서를 찾지 못했습니다."

    context = context[:MAX_CONTEXT_LENGTH]

    system_prompt = f"""
너는 한국어 ICT 면접 시뮬레이터 AI다.

[절대 규칙]
- 반드시 한국어로만 답변한다.
- 중국어, 일본어, 아랍어, 영어 문장을 출력하지 않는다.
- 한자, 중국어 문자, 아랍어 문자가 섞이면 안 된다.
- Context에 있는 정보만 사용한다.
- Context에 답이 없으면 "제공된 자료에서 확인할 수 없습니다."라고 답한다.
- 답변은 3문장 이내로 짧고 명확하게 작성한다.

[Context]
{context}
""".strip()

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    for msg in req.history:
        messages.append({
            "role": msg.role,
            "content": msg.content,
        })

    messages.append({
        "role": "user",
        "content": req.question,
    })

    print("\n" + "=" * 80)
    print("OLLAMA REQUEST DEBUG")
    print("=" * 80)
    print("MODEL:", model)
    print("PERSONA:", req.persona)
    print("QUESTION:", req.question)
    print("CONTEXT LENGTH:", len(context))
    print("HISTORY COUNT:", len(req.history))
    print("TOTAL MESSAGE CHARS:", sum(len(m["content"]) for m in messages))
    print("-" * 80)
    print(json.dumps(messages, ensure_ascii=False, indent=2))
    print("=" * 80 + "\n")

    answer = chat_with_ollama(model, messages)

    return {
        "persona": req.persona,
        "model": model,
        "answer": answer,
    }