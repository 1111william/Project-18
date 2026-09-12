from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers import quizzes, progress


app = FastAPI(
    title="Bangla Learning Platform API",
    version="0.1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    quizzes.router,
    prefix="/api/quizzes",
    tags=["Quiz"]
)

app.include_router(
    progress.router,
    prefix="/api/progress",
    tags=["Progress"]
)


@app.get("/")
def root():
    return {
        "message": "Bangla Learning Platform API"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok"
    }