from typing import List, Literal, Optional
from pydantic import BaseModel, Field

Persona = Literal["friendly", "pressure"]
Stage = Literal["idle", "setup", "interview", "feedback", "feedback_ready"]


class ChatMessage(BaseModel):
    role: str
    content: str


class ModelRouteRequest(BaseModel):
    stage: Stage = "idle"
    persona: Persona = "friendly"
    question: str = ""


class ModelRouteResponse(BaseModel):
    stage: Stage
    persona: Persona
    model: str


class ChatRequest(BaseModel):
    stage: Stage = "interview"
    persona: Persona = "friendly"
    question: str
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    stage: Stage
    persona: Persona
    model: str
    answer: str


class CreateSessionRequest(BaseModel):
    user_id: str
    persona: Persona = "friendly"
    job_role: str = "ICT"
    question_count: int = 5
    resume_text: Optional[str] = ""
    job_post_text: Optional[str] = ""


class CreateSessionResponse(BaseModel):
    session_id: str
    user_id: str
    persona: Persona
    job_role: str
    question_count: int
    status: str

class StartInterviewResponse(BaseModel):
    session_id: str
    status: str
    question_index: int
    question: str
    model: str

class SubmitAnswerRequest(BaseModel):
    answer: str


class SubmitAnswerResponse(BaseModel):
    session_id: str
    status: str
    question_index: int
    answer_saved: bool
    next_question: str = ""
    model: str = ""
    message: str = ""
    feedback: str = ""

class FeedbackResponse(BaseModel):
    session_id: str
    status: str
    model: str
    feedback: str