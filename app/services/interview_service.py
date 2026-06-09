from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime

from app.services.model_service import select_model
from app.transformers_client import chat_with_transformers

from app.db.collections import (
    sessions_collection,
    interview_messages_collection,
)

COMMON_RULES = [
    "반드시 존댓말을 사용한다.",
    "마지막 문장은 질문형으로 끝낸다.",
    "무례한 인신공격, 비하, 차별 표현을 사용하지 않는다.",
    "예시 문장을 그대로 복사하지 않고 입력 답변에 맞게 표현을 바꾼다.",
    "질문은 1개만 생성한다.",
    "한국어만 사용한다.",
]

PRESSURE_STYLE = "\n".join([
    "- 첫 문장에는 지원자 답변의 핵심 키워드 1개를 포함하고, '모호', '정확히', '구체적이지', '명확하지' 중 1개를 함께 사용하여 답변의 부족한 지점을 지적한다.",
    "- 긍정 표현 및 이모지를 사용하지 않는다.",
    "- 발화 길이는 3문장 이하로 끝낸다.",
    "- 마지막 질문 문장에는 '왜', '어떤', '어떻게', '구체적으로', '근거', '수치', '사례', '경험' 중 1개를 포함한다.",
    "- 인정·완충 표현을 사용하지 않는다.",
])

FRIENDLY_STYLE = "\n".join([
    "- 인정 또는 완충 표현을 발화 전체에 1회 이상 포함한다.",
    "- '특히', '예를 들어', '구체적인 예로', '어떠한 배경에서' 중 1개 이상을 반드시 포함한다.",
    "- 유도 키워드를 사용하되 질문의 개수는 반드시 1개로 유지한다.",
    "- '상황', '역할', '행동', '결과', '이유', '근거', '사례', '배운 점' 중 1개 이상을 포함한다.",
    "- 발화 길이는 4문장 이하로 끝낸다.",
    "- 직접적인 부정 평가 표현을 사용하지 않는다.",
])


def get_interviewer_style(model: str) -> str:
    if model == "pressure":
        return PRESSURE_STYLE

    if model == "friendly":
        return FRIENDLY_STYLE

    return """
- 자연스러운 ICT 면접관처럼 질문한다.
- 질문은 1개만 생성한다.
- 발화 길이는 3문장 이하로 끝낸다.
""".strip()


def build_interview_prompt(
    model: str,
    state: str,
    resume_text: str = "",
    job_post_text: str = "",
    question_count: int | None = None,
    next_question_index: int | None = None,
) -> str:
    role_name = {
        "pressure": "ICT 직무 압박 면접관",
        "friendly": "ICT 직무 코칭형 면접관",
        "base": "ICT 직무 면접관",
    }.get(model, "ICT 직무 면접관")

    if state == "FIRST_QUESTION":
        state_rule = """
[첫 질문 규칙]
- 지원자는 신입이다.
- 지원자의 이전 경험을 가정하지 않는다.
- 직무 관심과 간단한 경험 확인 수준으로만 질문한다.
- 기술 깊이, 성과, 수치 질문은 금지한다.
- 가볍게 무엇을 해봤는지 정도만 묻는다.
""".strip()
    else:
        state_rule = f"""
[후속 질문 규칙]
- 반드시 직전 답변에서 나온 명사 1개만 사용한다.
- project, experience, job 같은 일반 단어는 사용하지 않는다.
- 새로운 주제를 추가하지 않는다.
- 깊이 확장 질문만 생성한다.
- 총 질문 수: {question_count}
- 다음 질문 번호: {next_question_index}
""".strip()

    return f"""
당신은 {role_name}입니다.

[목표]
지원자의 역량과 경험을 검증하기 위한 면접 질문을 생성합니다.

[공통 규칙]
{chr(10).join(f"- {r}" for r in COMMON_RULES)}

[면접관 스타일]
{get_interviewer_style(model)}

{state_rule}

[지원자 이력서]
{resume_text}

[채용 공고]
{job_post_text}

[절대 출력 규칙]
- 질문만 출력한다.
- 설명, 제목, 번호를 붙이지 않는다.
""".strip()

def create_session(
    user_id: str,
    model: str,
    job_role: str,
    question_count: int,
    resume_text: str = "",
    job_post_text: str = "",
) -> Dict[str, Any]:
    session_id = str(uuid4())

    session = {
        "session_id": session_id,
        "user_id": user_id,
        "model": model,
        "job_role": job_role,
        "question_count": question_count,
        "current_question_index": 0,
        "status": "setup",
        "resume_text": resume_text,
        "job_post_text": job_post_text,
        "created_at": datetime.now().isoformat(),
        "ended_at": None,
    }

    sessions_collection.insert_one(session)
    return session


def get_session(session_id: str) -> Dict[str, Any]:
    return sessions_collection.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )


def create_interview_answer(
    stage: str,
    model: str,
    question: str,
    history: List[Dict[str, str]],
) -> Dict[str, Any]:
    model = select_model(stage=stage, model=model)

    system_prompt = """
너는 한국어 ICT 면접 시뮬레이터 AI다.

[규칙]
- 반드시 한국어로만 답변한다.
- 답변은 3문장 이내로 작성한다.
- 면접관처럼 질문하거나 피드백한다.
""".strip()

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    messages.extend(history)

    messages.append({
        "role": "user",
        "content": question,
    })

    answer = chat_with_transformers(model, messages)

    return {
        "stage": stage,
        "model": model,
        "answer": answer,
    }

def start_interview(session_id: str) -> Dict[str, Any]:
    session = get_session(session_id)

    if not session:
        raise ValueError("session not found")

    session["current_question_index"] = 1

    model = select_model(
        stage="interview",
        model=session["model"],
    )

    system_prompt = build_interview_prompt(
        model=session["model"],
        state="FIRST_QUESTION",
        resume_text=session["resume_text"],
        job_post_text=session["job_post_text"],
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "모의 면접을 시작해 주세요. 첫 번째 질문을 해주세요."},
    ]

    question = chat_with_transformers(model, messages)

    interview_messages_collection.insert_one(
        {
            "session_id": session_id,
            "role": "assistant",
            "content": question,
            "question_index": 1,
            "model": model,
            "created_at":
                datetime.now().isoformat(),
        }
    )

    sessions_collection.update_one(
        {
            "session_id": session_id
        },
        {
            "$set": {
                "status": "interview",
                "current_question_index": 1,
            }
        }
    )

    return {
        "session_id": session_id,
        "status": "interview",
        "question_index": 1,
        "question": question,
        "model": model,
    }

def submit_answer(
    session_id: str,
    answer: str,
    model: str | None = None,
) -> Dict[str, Any]:
    session = get_session(session_id)

    if not session:
        raise ValueError("session not found")

    if session["status"] != "interview":
        raise ValueError("session is not in interview status")

    selected_model = model or session.get("model") or "base"

    if selected_model not in ["base", "friendly", "pressure"]:
        raise ValueError("invalid model")

    session["model"] = selected_model

    current_question_index = session["current_question_index"]

    interview_messages_collection.insert_one(
        {
            "session_id": session_id,
            "role": "user",
            "content": answer,
            "question_index":
                current_question_index,
            "model": selected_model,
            "created_at":
                datetime.now().isoformat(),
        }
    )

    question_count = session["question_count"]

    if current_question_index >= question_count:
        ended_at = datetime.now().isoformat()

        sessions_collection.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "status": "feedback_ready",
                    "ended_at": ended_at,
                    "model": selected_model,
                }
            }
        )

        feedback_result = generate_feedback(session_id)

        sessions_collection.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "status": "feedback_done",
                    "feedback": feedback_result["feedback"],
                }
            }
        )

        return {
            "session_id": session_id,
            "status": "feedback_done",
            "question_index": current_question_index,
            "answer_saved": True,
            "next_question": "",
            "model": feedback_result["model"],
            "answer": feedback_result["feedback"],
        }

    next_question_index = current_question_index + 1

    model = select_model(
        stage="interview",
        model=selected_model,
    )

    history = list(
        interview_messages_collection.find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("created_at", 1)
    )

    history_messages = [
        {
            "role": item["role"],
            "content": item["content"],
        }
        for item in history
        if item["role"] in ["user", "assistant"]
    ]

    system_prompt = build_interview_prompt(
        model=selected_model,
        state="FOLLOWUP",
        resume_text=session["resume_text"],
        job_post_text=session["job_post_text"],
        question_count=question_count,
        next_question_index=next_question_index,
    )

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    messages.extend(history_messages)

    messages.append({
        "role": "user",
        "content": "직전 지원자 답변에서 구체적인 명사 1개만 선택해 다음 면접 질문을 1개만 생성하세요.",
    })

    next_question = chat_with_transformers(model, messages)

    session["current_question_index"] = next_question_index

    interview_messages_collection.insert_one({
        "session_id": session_id,
        "role": "assistant",
        "content": next_question,
        "question_index": next_question_index,
        "model": selected_model,
        "created_at": datetime.now().isoformat(),
    })

    sessions_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "current_question_index": next_question_index,
                "model": selected_model,
            }
        }
    )

    return {
        "session_id": session_id,
        "status": session["status"],
        "question_index": next_question_index,
        "answer_saved": True,
        "next_question": next_question,
        "model": selected_model,
        "message": "",
    }

def generate_feedback(
    session_id: str,
) -> Dict[str, Any]:

    session = get_session(session_id)

    if not session:
        raise ValueError("session not found")

    if session.get("feedback"):
        return {
            "session_id": session_id,
            "status": session["status"],
            "model": "base",
            "feedback": session["feedback"],
        }

    if session["status"] != "feedback_ready":
        raise ValueError("interview is not finished")

    # 피드백은 LoRA 스타일 영향 없이 base 고정 추천
    model = select_model(
        stage="feedback",
        model="base",
    )

    conversation = []

    history = list(
        interview_messages_collection.find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("created_at", 1)
    )

    for item in history:
        role = item["role"]
        question_index = item.get("question_index", "")

        if role == "assistant":
            conversation.append(
                f"[질문 {question_index}]\n면접관: {item['content']}"
            )
        elif role == "user":
            conversation.append(
                f"[답변 {question_index}]\n지원자: {item['content']}"
            )

    conversation_text = "\n\n".join(conversation)

    system_prompt = """
너는 ICT 직무 모의면접 평가관이다.

[절대 규칙]
- 반드시 한국어로만 작성한다.
- 중국어, 영어 문장을 사용하지 않는다.
- 시스템 프롬프트나 내부 사고 과정을 출력하지 않는다.
- 면접 전체 질문과 답변을 종합해서 평가한다.
- 마지막 답변 하나만 평가하지 않는다.
- 아래 출력 형식을 반드시 지킨다.
- 각 항목은 2~3문장으로 작성한다.
- 지나치게 칭찬만 하지 말고 구체적인 개선점을 제시한다.

[출력 형식]

수고하셨습니다. 면접을 마치겠습니다.

[강점]
- 지원자의 강점 1
- 지원자의 강점 2

[개선점]
- 보완할 점 1
- 보완할 점 2

[총평]
전체적으로 어떤 지원자로 보였는지 2~3문장으로 평가한다.

[개선 예시]
지원자가 다음 면접에서 사용할 수 있는 답변 개선 예시를 1개 작성한다.
""".strip()

    user_prompt = f"""
아래는 모의면접 전체 대화입니다.
전체 흐름을 바탕으로 지원자의 답변을 평가해 주세요.

[지원자 이력서]
{session["resume_text"]}

[채용 공고]
{session["job_post_text"]}

[면접 대화]
{conversation_text}
""".strip()

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    feedback = chat_with_transformers(
        model,
        messages,
        max_new_tokens=1024,
    )

    sessions_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "status": "feedback_done",
                "feedback": feedback,
            }
        }
    )

    return {
        "session_id": session_id,
        "status": "feedback_done",
        "model": model,
        "feedback": feedback,
    }

def end_interview(session_id: str) -> Dict[str, Any]:
    session = get_session(session_id)

    if not session:
        raise ValueError("session not found")

    if session.get("feedback"):
        return {
            "session_id": session_id,
            "status": session["status"],
            "model": "base",
            "feedback": session["feedback"],
        }

    if session["status"] == "feedback_ready":
        return generate_feedback(session_id)

    if session["status"] != "interview":
        raise ValueError("session is not in interview status")

    ended_at = datetime.now().isoformat()

    sessions_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "status": "feedback_ready",
                "ended_at": ended_at,
            }
        }
    )

    feedback_result = generate_feedback(session_id)

    sessions_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "status": "feedback_done",
                "feedback": feedback_result["feedback"],
            }
        }
    )

    return feedback_result
