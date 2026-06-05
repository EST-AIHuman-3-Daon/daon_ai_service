from typing import List, Dict, Any
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel


BASE_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

BASE_DIR = Path(__file__).resolve().parent.parent

LORA_PATHS = {
    "friendly": str(
        BASE_DIR
        / "models"
        / "lora"
        / "qwen2.5-7B-instruct_friendly"
    ),
    "pressure": str(
        BASE_DIR
        / "models"
        / "lora"
        / "qwen2.5-7B-instruct_pressure"
    ),
}

for name, path in LORA_PATHS.items():
    print(f"{name}: {path}")
    print("adapter_config exists:", Path(path, "adapter_config.json").exists())
    print("adapter_model exists:", Path(path, "adapter_model.safetensors").exists())

device = (
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)

base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_ID,
    dtype=torch.float16 if device == "mps" else torch.float32,
).to(device)

llm = PeftModel.from_pretrained(
    base_model,
    LORA_PATHS["friendly"],
    adapter_name="friendly",
).to(device)

llm.load_adapter(
    LORA_PATHS["pressure"],
    adapter_name="pressure",
)

llm.eval()


def chat_with_transformers(
    model_name: str,
    messages: List[Dict[str, Any]],
) -> str:
    try:
        adapter_name = model_name

        if adapter_name not in LORA_PATHS:
            adapter_name = "friendly"

        llm.set_adapter(adapter_name)

        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = tokenizer(
            prompt,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            outputs = llm.generate(
                **inputs,
                max_new_tokens=80,
                temperature=0.2,
                top_p=0.8,
                repetition_penalty=1.2,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        generated_tokens = outputs[0][inputs["input_ids"].shape[-1]:]

        return tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        ).strip()

    except Exception as e:
        raise RuntimeError(f"Transformers 호출 실패: {e}")