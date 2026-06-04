from typing import Literal

Persona = Literal["friendly", "pressure"]

Stage = Literal[
    "idle",
    "interview",
    "feedback",
    "feedback_ready",
]

MODEL_MAP = {
    "idle": "friendly",
    "feedback": "friendly",
    "feedback_ready": "friendly",
    "friendly": "friendly",
    "pressure": "pressure",
}


def select_model(
    stage: Stage,
    persona: Persona = "friendly",
) -> str:
    if stage == "interview":
        return MODEL_MAP.get(persona, "friendly")

    return MODEL_MAP.get(stage, "friendly")