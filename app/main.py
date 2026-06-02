from fastapi import FastAPI

from app.routers import interview

app = FastAPI()

app.include_router(interview.router)


@app.get("/")
def health_check():
    return {"message": "Daon AI service is running"}