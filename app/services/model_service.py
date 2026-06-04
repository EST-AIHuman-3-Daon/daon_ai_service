from typing import Literal

ModelName = Literal[
    "base",
    "friendly",
    "pressure",
]

Stage = Literal[
    "idle",
    "interview",
    "feedback",
    "feedback_ready",
]

MODEL_MAP = {
    "idle": "base",
    "feedback": "base",
    "feedback_ready": "base",

    "base": "base",
    "friendly": "friendly",
    "pressure": "pressure",
}


def select_model(
    stage: str,
    model: str = "base",
) -> str:
    if stage == "interview":
        return MODEL_MAP.get(model, "friendly")

    return MODEL_MAP.get(stage, "base")