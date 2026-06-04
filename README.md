# AI 면접 시뮬레이터 Serving Server

FastAPI 기반 AI 면접 시뮬레이터 서버입니다.
지원자의 이력서와 채용공고 정보를 바탕으로 면접 질문을 생성하고, 답변에 따라 다음 질문 또는 꼬리질문을 생성합니다.
면접이 종료되면 전체 대화 내용을 기반으로 피드백을 생성합니다.

## 주요 기능

- 면접 세션 생성
- 면접 시작 및 첫 질문 생성
- 답변 제출
- 다음 질문 / 꼬리질문 생성
- `base`, `friendly`, `pressure` 모델 선택
- 면접 종료 후 자동 피드백 생성
- FastAPI Swagger 문서 제공

## 개발 환경

```bash
Python 3.10
```

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd EST_AIHuman_3_Daon_AI_Serving
```

### 2. 가상환경 생성 및 활성화

```bash
python3.10 -m venv venv
source venv/bin/activate
```

Windows PowerShell:

```powershell
py -3.10 -m venv venv
venv\Scripts\Activate.ps1
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

필요 시 직접 설치:

```bash
pip install fastapi uvicorn transformers torch peft safetensors accelerate
```

## LoRA 모델 준비

LoRA 파일은 아래 구조로 배치합니다.

```text
models/
└── lora/
    ├── qwen2.5-7B-instruct_friendly/
    │   ├── adapter_config.json
    │   └── adapter_model.safetensors
    └── qwen2.5-7B-instruct_pressure/
        ├── adapter_config.json
        └── adapter_model.safetensors
```

`safetensors` 파일이 정상인지 확인:

```bash
python - <<'PY'
from safetensors import safe_open

paths = [
    "models/lora/qwen2.5-7B-instruct_friendly/adapter_model.safetensors",
    "models/lora/qwen2.5-7B-instruct_pressure/adapter_model.safetensors",
]

for path in paths:
    print("checking:", path)
    with safe_open(path, framework="pt", device="cpu") as f:
        print("OK", len(f.keys()))
PY
```

## 서버 실행

```bash
uvicorn app.main:app --reload
```

정상 실행 시:

```text
Uvicorn running on http://127.0.0.1:8000
```

Swagger 문서:

```text
http://localhost:8000/docs
```

## API 테스트 순서

### 1. 세션 생성

```bash
curl -X POST http://localhost:8000/interview/sessions \
-H "Content-Type: application/json" \
-d '{
  "user_id": "user_001",
  "model": "friendly",
  "job_role": "ICT",
  "question_count": 3,
  "resume_text": "React, TypeScript, Express, AWS 배포 경험이 있습니다.",
  "job_post_text": "ICT 개발 직무. 웹 서비스 개발, API 연동, 클라우드 배포 경험을 우대합니다."
}'
```

응답의 `session_id`를 복사합니다.

### 2. 면접 시작

```bash
curl -X POST \
http://localhost:8000/interview/sessions/SESSION_ID/start
```

### 3. 답변 제출 - friendly

```bash
curl -X POST \
http://localhost:8000/interview/sessions/SESSION_ID/answer \
-H "Content-Type: application/json" \
-d '{
  "answer": "React와 Express를 사용해 개인 웹사이트를 개발했습니다."
}'
```

### 4. 답변 제출 - pressure LoRA

```bash
curl -X POST \
http://localhost:8000/interview/sessions/SESSION_ID/answer \
-H "Content-Type: application/json" \
-d '{
  "answer": "이미지 로딩 속도 개선을 위해 캐싱을 적용했습니다.",
  "model": "pressure"
}'
```

### 5. 답변 제출 - base 모델

```bash
curl -X POST \
http://localhost:8000/interview/sessions/SESSION_ID/answer \
-H "Content-Type: application/json" \
-d '{
  "answer": "세션 인증과 권한 검사를 서버에서 처리했습니다.",
  "model": "base"
}'
```

`question_count`가 3이면 세 번째 답변 이후 자동으로 피드백이 생성됩니다.

### 6. 세션 조회

```bash
curl \
http://localhost:8000/interview/sessions/SESSION_ID
```

## 모델 옵션

| model      | 설명                           |
| ---------- | ------------------------------ |
| `base`     | LoRA를 적용하지 않은 기본 모델 |
| `friendly` | 친절한 면접관 LoRA             |
| `pressure` | 압박 면접관 LoRA               |

## 주의사항

- `adapter_model.safetensors` 파일이 깨져 있으면 서버 실행 시 오류가 발생합니다.
- LoRA는 학습에 사용한 base model과 동일 계열 모델에 연결해야 합니다.
- Mac 환경에서는 모델 로딩 시 메모리를 많이 사용할 수 있습니다.
- `--reload` 옵션 사용 시 모델이 재로딩될 수 있어 개발 중 메모리 사용량에 주의해야 합니다.
