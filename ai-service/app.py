from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

from routes.explain import router as explain_router
from routes.quiz import router as quiz_router
from routes.recommendation import router as recommendation_router
from routes.planner import router as planner_router
from routes.evaluation import router as evaluation_router
from routes.analytics import router as analytics_router

app = FastAPI(title="Athenix AI Service")

app.include_router(explain_router)
app.include_router(quiz_router)
app.include_router(recommendation_router)
app.include_router(planner_router)
app.include_router(evaluation_router)
app.include_router(analytics_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Athenix AI Service"}
