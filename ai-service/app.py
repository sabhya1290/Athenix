from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

from routes.explain import router as explain_router
from routes.quiz import router as quiz_router

app = FastAPI(title="Athenix AI Service")

app.include_router(explain_router)
app.include_router(quiz_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Athenix AI Service"}
