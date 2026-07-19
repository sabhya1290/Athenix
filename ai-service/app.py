# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
import os

load_dotenv()

from routes.explain import router as explain_router
from routes.quiz import router as quiz_router
from routes.recommendation import router as recommendation_router
from routes.planner import router as planner_router
from routes.evaluation import router as evaluation_router
from routes.analytics import router as analytics_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Athenix AI Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to match your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(explain_router)
app.include_router(quiz_router)
app.include_router(recommendation_router)
app.include_router(planner_router)
app.include_router(evaluation_router)
app.include_router(analytics_router)

# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from utils.response import UnifiedResponse

class HealthResponse(BaseModel):
    status: str
    service: str

@app.get("/health", response_model=UnifiedResponse[HealthResponse])
def health_check():
    return UnifiedResponse(
        success=True,
        data=HealthResponse(status="healthy", service="Athenix AI Service")
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to Athenix AI Service"}
