from typing import Literal

Persona = Literal["friendly", "pressure"]

Stage = Literal[
    "idle",
    "interview",
    "feedback",
    "feedback_ready",
]

MODEL_MAP = {
    # "idle": "qwen3.5:9b",
    # "feedback": "qwen3.5:9b",
    # "friendly": "ict-friendly",
    # "pressure": "ict-pressure",

    "idle": "qwen2.5:7b",
    "feedback": "qwen2.5:7b",
    "friendly": "qwen2.5:7b",
    "pressure": "qwen2.5:7b",
}


def select_model(
    stage: Stage,
    persona: Persona = "friendly",
) -> str:

    if stage == "interview":
        return MODEL_MAP.get(
            persona,
            MODEL_MAP["friendly"],
        )

    if stage in ["idle", "feedback", "feedback_ready"]:
        return MODEL_MAP.get(
            stage,
            MODEL_MAP["idle"],
        )

    return MODEL_MAP["idle"]