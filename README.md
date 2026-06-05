# Daon AI Interview Serving Server

FastAPI 기반 AI 면접 시뮬레이터 서버입니다. 지원자의 이력서와 채용공고를 바탕으로 면접 질문을 생성하고, 답변 흐름에 따라 다음 질문 또는 꼬리질문을 생성합니다. 면접이 종료되면 전체 대화 내용을 기반으로 피드백을 생성합니다.

## 주요 기능

- 면접 세션 생성 및 조회
- 이력서/채용공고 기반 첫 질문 생성
- 지원자 답변 저장
- 이전 대화 흐름 기반 다음 질문 생성
- `base`, `friendly`, `pressure` 모델 선택
- 면접 종료 후 전체 대화 기반 피드백 생성
- MongoDB 기반 세션 및 메시지 저장
- FastAPI Swagger 문서 제공

## 기술 스택

- Python 3.10
- FastAPI
- Uvicorn
- MongoDB / PyMongo
- Transformers
- PEFT / LoRA
- PyTorch
- Qwen2.5-7B-Instruct

## 프로젝트 구조

```text
.
├── app/
│   ├── core/
│   │   └── config.py              # 환경 변수 로딩
│   ├── db/
│   │   ├── collections.py         # MongoDB 컬렉션 및 인덱스
│   │   └── mongodb.py             # MongoDB 클라이언트
│   ├── routers/
│   │   └── interview.py           # 면접 API 라우터
│   ├── schemas/
│   │   └── interview.py           # 요청/응답 Pydantic 스키마
│   ├── services/
│   │   ├── interview_service.py   # 면접 세션, 질문, 피드백 로직
│   │   └── model_service.py       # stage/model 라우팅
│   ├── main.py                    # FastAPI 앱 엔트리포인트
│   ├── rag.py                     # RAG 관련 유틸리티
│   └── transformers_client.py     # Transformers/LoRA 모델 호출
├── docs/                          # RAG 문서 배치 위치
├── models/                        # LoRA 모델 파일 배치 위치
├── vector_db/                     # 벡터 DB 저장 위치
├── requirements.txt
└── README.md
```

## 실행 준비

### 1. 저장소 클론

```bash
git clone https://github.com/EST-AIHuman-3-Daon/daon_ai_service.git
cd daon_ai_service
```

### 2. 가상환경 생성 및 활성화

macOS/Linux:

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

### 4. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다.

```env
MONGODB_URI=mongodb://localhost:27017
```

MongoDB Atlas를 사용하는 경우 Atlas 접속 문자열을 넣으면 됩니다.

```env
MONGODB_URI=mongodb+srv://USER:PASSWORD@HOST/main_db?retryWrites=true&w=majority
```

### 5. MongoDB 준비

로컬 MongoDB를 사용하는 경우 MongoDB 서버가 실행 중이어야 합니다.

```bash
brew services start mongodb-community
```

MongoDB가 준비되지 않으면 서버 시작 또는 API 호출 시 DB 연결 오류가 발생할 수 있습니다.

### 6. LoRA 모델 준비

이 프로젝트는 기본 모델로 `Qwen/Qwen2.5-7B-Instruct`를 사용하고, `friendly`, `pressure` LoRA adapter를 로컬에서 로딩합니다. LoRA 파일은 아래 위치에 배치해야 합니다.

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

모델 파일은 용량이 커서 Git에 포함하지 않습니다. 테스트하는 사람은 위 구조대로 파일을 직접 받아서 배치해야 합니다.

`adapter_model.safetensors` 파일 확인:

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
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

개발 중 자동 재시작이 필요하면 아래 명령을 사용할 수 있습니다.

```bash
uvicorn app.main:app --reload
```

단, `--reload`는 코드 변경 시 모델을 다시 로딩할 수 있어 메모리 사용량이 커질 수 있습니다.

서버가 실행되면 아래 주소에서 문서를 확인할 수 있습니다.

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/`

## 빠른 API 테스트

아래 순서대로 실행하면 다른 사람도 기본 면접 흐름을 테스트할 수 있습니다.

### 1. 세션 생성

```bash
curl -X POST http://localhost:8000/interview/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "model": "friendly",
    "job_role": "ICT 개발자",
    "question_count": 3,
    "resume_text": "React, TypeScript, Express, AWS 배포 경험이 있습니다.",
    "job_post_text": "웹 서비스 개발, API 연동, 클라우드 배포 경험을 우대합니다."
  }'
```

응답 예시:

```json
{
  "session_id": "SESSION_ID",
  "user_id": "user_001",
  "model": "friendly",
  "job_role": "ICT 개발자",
  "question_count": 3,
  "status": "setup"
}
```

응답의 `session_id`를 다음 요청에 사용합니다.

### 2. 면접 시작

```bash
curl -X POST http://localhost:8000/interview/sessions/SESSION_ID/start
```

응답 예시:

```json
{
  "session_id": "SESSION_ID",
  "status": "interview",
  "question_index": 1,
  "question": "첫 번째 면접 질문입니다.",
  "model": "friendly"
}
```

### 3. 답변 제출

```bash
curl -X POST http://localhost:8000/interview/sessions/SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "React와 Express를 사용해 개인 웹사이트를 개발했고, AWS에 배포했습니다."
  }'
```

응답의 `next_question`에 다음 질문이 담깁니다.

### 4. 모델 스타일 변경 후 답변 제출

```bash
curl -X POST http://localhost:8000/interview/sessions/SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "이미지 로딩 속도 개선을 위해 캐싱과 lazy loading을 적용했습니다.",
    "model": "pressure"
  }'
```

### 5. 마지막 답변 제출 및 자동 피드백 생성

`question_count`가 3이면 세 번째 답변 제출 후 자동으로 피드백이 생성됩니다.

```bash
curl -X POST http://localhost:8000/interview/sessions/SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "세션 인증과 권한 검사를 서버에서 처리해 보안을 강화했습니다.",
    "model": "base"
  }'
```

### 6. 세션 조회

```bash
curl http://localhost:8000/interview/sessions/SESSION_ID
```

### 7. 면접 수동 종료

질문 수를 모두 채우기 전에 면접을 종료하고 피드백을 생성할 수 있습니다.

```bash
curl -X POST http://localhost:8000/interview/sessions/SESSION_ID/end
```

### 8. 피드백 조회/생성

면접 상태가 `feedback_ready`이거나 이미 피드백이 생성된 경우 사용할 수 있습니다.

```bash
curl -X POST http://localhost:8000/interview/sessions/SESSION_ID/feedback
```

## API 요약

| Method | Endpoint | 설명 |
| ------ | -------- | ---- |
| GET | `/` | 서버 상태 확인 |
| POST | `/interview/model-route` | stage/model 입력에 따른 모델 라우팅 확인 |
| POST | `/interview/chat` | 세션 없이 단일 채팅 응답 생성 |
| POST | `/interview/sessions` | 면접 세션 생성 |
| GET | `/interview/sessions/{session_id}` | 면접 세션 및 저장된 상태 조회 |
| POST | `/interview/sessions/{session_id}/start` | 면접 시작 및 첫 질문 생성 |
| POST | `/interview/sessions/{session_id}/answer` | 답변 저장 및 다음 질문 또는 피드백 생성 |
| POST | `/interview/sessions/{session_id}/feedback` | 면접 피드백 생성 또는 기존 피드백 반환 |
| POST | `/interview/sessions/{session_id}/end` | 면접 수동 종료 및 피드백 생성 |

## 요청/응답 모델

### 모델 옵션

| model | 설명 |
| ----- | ---- |
| `base` | LoRA를 적용하지 않은 기본 모델 |
| `friendly` | 친절한 면접관 스타일 LoRA |
| `pressure` | 압박 면접관 스타일 LoRA |

### 세션 상태

| status | 설명 |
| ------ | ---- |
| `setup` | 세션 생성 후 면접 시작 전 |
| `interview` | 면접 진행 중 |
| `feedback_ready` | 면접 종료 후 피드백 생성 가능 상태 |
| `feedback_done` | 피드백 생성 완료 |

### `POST /interview/sessions` 요청 필드

| 필드 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- |
| `user_id` | string | 예 | 사용자 식별자 |
| `model` | string | 아니오 | `base`, `friendly`, `pressure`; 기본값 `friendly` |
| `job_role` | string | 아니오 | 지원 직무; 기본값 `ICT` |
| `question_count` | integer | 아니오 | 질문 개수; 1~10, 기본값 5 |
| `resume_text` | string | 아니오 | 이력서 내용 |
| `job_post_text` | string | 아니오 | 채용공고 내용 |

### `POST /interview/sessions/{session_id}/answer` 요청 필드

| 필드 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- |
| `answer` | string | 예 | 지원자의 답변 |
| `model` | string | 아니오 | 다음 질문 생성에 사용할 모델 스타일 |

## 테스트 체크리스트

서버를 실행하기 전에 아래 항목을 확인합니다.

- Python 3.10 환경인지 확인
- `pip install -r requirements.txt` 완료
- `.env`에 `MONGODB_URI` 설정
- MongoDB 서버 또는 Atlas 접근 가능
- `models/lora/...` 아래 LoRA adapter 파일 배치
- 첫 실행 시 Hugging Face 모델 다운로드가 가능하거나 캐시에 존재
- Mac 환경에서는 충분한 메모리 확보

## 개발 참고사항

- `app/transformers_client.py`는 import 시점에 base model과 LoRA adapter를 로딩합니다. 서버 시작이 느릴 수 있습니다.
- `friendly`, `pressure` adapter는 하나의 전역 모델 인스턴스에서 전환해 사용합니다. 동시 요청에서 adapter가 섞이지 않도록 generation 구간은 lock으로 보호합니다.
- 모델 파일, 벡터 DB, `.env`는 Git에 포함하지 않습니다.
- 현재 RAG 유틸리티는 `app/rag.py`에 있으나, 주요 면접 API 흐름에는 직접 연결되어 있지 않습니다.

## 자주 발생하는 문제

### `MONGODB_URI 환경변수가 설정되지 않았습니다.`

`.env` 파일에 `MONGODB_URI`를 추가했는지 확인합니다.

### `adapter_config.json` 또는 `adapter_model.safetensors` 관련 오류

LoRA 파일 경로가 README의 구조와 같은지 확인합니다.

### 서버 시작이 오래 걸림

7B 모델과 LoRA adapter를 서버 시작 시 로딩하기 때문에 시간이 걸릴 수 있습니다. 첫 실행에서는 Hugging Face 모델 다운로드 시간도 포함됩니다.

### `--reload` 사용 시 메모리 사용량 증가

코드가 변경될 때마다 모델이 다시 로딩될 수 있습니다. 모델 테스트 중에는 `--reload` 없이 실행하는 것을 권장합니다.
