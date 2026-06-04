from fastapi import APIRouter, HTTPException

from app.schemas.interview import (
    ModelRouteRequest,
    ModelRouteResponse,
    ChatRequest,
    ChatResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    FeedbackResponse,
)
from app.services.interview_service import (
    create_interview_answer,
    create_session,
    get_session,
    start_interview,
    submit_answer,
    generate_feedback,
)

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/model-route", response_model=ModelRouteResponse)
def model_route(req: ModelRouteRequest):
    return {
        "stage": req.stage,
        "model": req.model,
    }


@router.post("/chat", response_model=ChatResponse)
def interview_chat(req: ChatRequest):
    history = [
        {
            "role": msg.role,
            "content": msg.content,
        }
        for msg in req.history
    ]

    return create_interview_answer(
        stage=req.stage,
        model=req.model,
        question=req.question,
        history=history,
    )


@router.post("/sessions", response_model=CreateSessionResponse)
def create_interview_session(req: CreateSessionRequest):
    session = create_session(
        user_id=req.user_id,
        model=req.model,
        job_role=req.job_role or "",
        question_count=req.question_count,
        resume_text=req.resume_text or "",
        job_post_text=req.job_post_text or "",
    )

    return {
        "session_id": session["session_id"],
        "user_id": session["user_id"],
        "model": session["model"],
        "job_role": session["job_role"],
        "question_count": session["question_count"],
        "status": session["status"],
    }


@router.get("/sessions/{session_id}")
def read_interview_session(session_id: str):
    session = get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    return session


@router.post("/sessions/{session_id}/start", response_model=StartInterviewResponse)
def start_interview_session(session_id: str):
    try:
        return start_interview(session_id)

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post("/sessions/{session_id}/answer", response_model=SubmitAnswerResponse)
def submit_interview_answer(
    session_id: str,
    req: SubmitAnswerRequest,
):
    try:
        return submit_answer(
            session_id=session_id,
            answer=req.answer,
            model=req.model,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post(
    "/sessions/{session_id}/feedback",
    response_model=FeedbackResponse,
)
def create_feedback(
    session_id: str,
):
    try:
        return generate_feedback(session_id)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )