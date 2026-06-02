from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime

from app.services.model_service import select_model
from app.ollama_client import chat_with_ollama


INTERVIEW_SESSIONS = {}


def create_session(
    user_id: str,
    persona: str,
    job_role: str,
    question_count: int,
    resume_text: str = "",
    job_post_text: str = "",
) -> Dict[str, Any]:
    session_id = str(uuid4())

    session = {
        "session_id": session_id,
        "user_id": user_id,
        "persona": persona,
        "job_role": job_role,
        "question_count": question_count,
        "current_question_index": 0,
        "status": "setup",
        "resume_text": resume_text,
        "job_post_text": job_post_text,
        "history": [],
        "created_at": datetime.now().isoformat(),
        "ended_at": None,
    }

    INTERVIEW_SESSIONS[session_id] = session
    return session


def get_session(session_id: str) -> Dict[str, Any]:
    return INTERVIEW_SESSIONS.get(session_id)


def create_interview_answer(
    stage: str,
    persona: str,
    question: str,
    history: List[Dict[str, str]],
) -> Dict[str, Any]:
    model = select_model(stage=stage, persona=persona)

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

    answer = chat_with_ollama(model, messages)

    return {
        "stage": stage,
        "persona": persona,
        "model": model,
        "answer": answer,
    }

def start_interview(session_id: str) -> Dict[str, Any]:
    session = get_session(session_id)

    if not session:
        raise ValueError("session not found")

    session["status"] = "interview"
    session["current_question_index"] = 1

    model = select_model(
        stage="interview",
        persona=session["persona"],
    )

    system_prompt = f"""
너는 한국어 ICT 면접관이다.

[면접관 스타일]
- persona: {session["persona"]}

[지원자 이력서]
{session["resume_text"]}

[채용 공고]
{session["job_post_text"]}

[규칙]
- 첫 번째 면접 질문을 생성한다.
- 질문은 1개만 생성한다.
- 반드시 한국어로 작성한다.
- 질문은 짧고 명확하게 작성한다.
""".strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "모의 면접을 시작해 주세요. 첫 번째 질문을 해주세요."},
    ]

    question = chat_with_ollama(model, messages)

    session["history"].append({
        "role": "assistant",
        "content": question,
        "question_index": 1,
        "created_at": datetime.now().isoformat(),
    })

    return {
        "session_id": session_id,
        "status": session["status"],
        "question_index": 1,
        "question": question,
        "model": model,
    }

def submit_answer(
    session_id: str,
    answer: str,
) -> Dict[str, Any]:
    session = get_session(session_id)

    if not session:
        raise ValueError("session not found")

    if session["status"] != "interview":
        raise ValueError("session is not in interview status")

    current_question_index = session["current_question_index"]

    # 1. 사용자 답변 저장
    session["history"].append({
        "role": "user",
        "content": answer,
        "question_index": current_question_index,
        "created_at": datetime.now().isoformat(),
    })

    # 2. 질문 개수 확인
    question_count = session["question_count"]

    # 3. 5개면 feedback 반환
    if current_question_index >= question_count:
        session["status"] = "feedback_ready"
        session["ended_at"] = datetime.now().isoformat()

        feedback_result = generate_feedback(session_id)

        session["status"] = "feedback_done"

        return {
            "session_id": session_id,
            "status": session["status"],
            "question_index": current_question_index,
            "answer_saved": True,
            "next_question": "",
            "model": feedback_result["model"],
            "message": "수고하셨습니다. 면접이 종료되었습니다.",
            "feedback": feedback_result["feedback"],
        }

    # 4. 5개 미만이면 다음 질문 생성
    next_question_index = current_question_index + 1

    model = select_model(
        stage="interview",
        persona=session["persona"],
    )

    history_messages = [
        {
            "role": item["role"],
            "content": item["content"],
        }
        for item in session["history"]
        if item["role"] in ["user", "assistant"]
    ]

    system_prompt = f"""
너는 한국어 ICT 면접관이다.

[면접관 스타일]
- persona: {session["persona"]}

[지원자 이력서]
{session["resume_text"]}

[채용 공고]
{session["job_post_text"]}

[현재 진행 상황]
- 총 질문 수: {question_count}
- 다음 질문 번호: {next_question_index}

[규칙]
- 이전 답변을 바탕으로 다음 면접 질문 또는 꼬리질문을 생성한다.
- 질문은 1개만 생성한다.
- 반드시 한국어로 작성한다.
- 질문은 짧고 명확하게 작성한다.
""".strip()

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    messages.extend(history_messages)

    messages.append({
        "role": "user",
        "content": "지원자의 마지막 답변을 바탕으로 다음 면접 질문을 1개 생성해 주세요.",
    })

    next_question = chat_with_ollama(model, messages)

    session["current_question_index"] = next_question_index

    session["history"].append({
        "role": "assistant",
        "content": next_question,
        "question_index": next_question_index,
        "created_at": datetime.now().isoformat(),
    })

    return {
        "session_id": session_id,
        "status": session["status"],
        "question_index": next_question_index,
        "answer_saved": True,
        "next_question": next_question,
        "model": model,
        "message": "",
    }

def generate_feedback(
    session_id: str,
) -> Dict[str, Any]:

    session = get_session(session_id)

    if not session:
        raise ValueError("session not found")

    if session["status"] != "feedback_ready":
        raise ValueError("interview is not finished")

    model = select_model(
        stage="feedback",
        persona=session["persona"],
    )

    conversation = []

    for item in session["history"]:
        role = item["role"]

        if role == "assistant":
            conversation.append(
                f"면접관: {item['content']}"
            )
        else:
            conversation.append(
                f"지원자: {item['content']}"
            )

    conversation_text = "\n\n".join(conversation)

    system_prompt = """
너는 ICT 면접 평가관이다.

[규칙]
- 반드시 한국어로 작성한다.
- 면접 전체 내용을 평가한다.
- 아래 형식으로 작성한다.

[강점]
...

[개선점]
...

[총평]
...
""".strip()

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": conversation_text,
        },
    ]

    feedback = chat_with_ollama(
        model,
        messages,
    )

    session["feedback"] = feedback

    return {
        "session_id": session_id,
        "status": session["status"],
        "model": model,
        "feedback": feedback,
    }