from fastapi import FastAPI

from app.db.collections import create_indexes
from app.routers import interview

app = FastAPI()

app.include_router(interview.router)


@app.on_event("startup")
def startup():
    create_indexes()


@app.get("/")
def health_check():
    return {"message": "Daon AI service is running"}
