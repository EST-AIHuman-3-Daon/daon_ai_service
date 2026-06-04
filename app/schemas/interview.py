from typing import List, Literal, Optional
from pydantic import BaseModel, Field


ModelName = Literal[
    "base",
    "friendly",
    "pressure",
]

Stage = Literal[
    "idle",
    "setup",
    "interview",
    "feedback",
    "feedback_ready",
]


class ChatMessage(BaseModel):
    role: str
    content: str


class ModelRouteRequest(BaseModel):
    stage: Stage = "idle"
    model: ModelName = "base"


class ModelRouteResponse(BaseModel):
    stage: Stage
    model: ModelName


class ChatRequest(BaseModel):
    stage: Stage = "interview"
    model: ModelName = "friendly"
    question: str
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    stage: Stage
    model: ModelName
    answer: str


class CreateSessionRequest(BaseModel):
    user_id: str
    model: ModelName = "friendly"
    job_role: str = "ICT"
    question_count: int = 5
    resume_text: Optional[str] = ""
    job_post_text: Optional[str] = ""


class CreateSessionResponse(BaseModel):
    session_id: str
    user_id: str
    model: ModelName
    job_role: str
    question_count: int
    status: str


class StartInterviewResponse(BaseModel):
    session_id: str
    status: str
    question_index: int
    question: str
    model: ModelName


class SubmitAnswerRequest(BaseModel):
    answer: str
    model: Optional[ModelName] = None


class SubmitAnswerResponse(BaseModel):
    session_id: str
    status: str
    question_index: int
    answer_saved: bool
    next_question: str = ""
    model: str = ""
    answer: str = ""


class FeedbackResponse(BaseModel):
    session_id: str
    status: str
    model: ModelName
    feedback: str