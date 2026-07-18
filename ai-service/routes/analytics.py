from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from services.gemini import generate_text
from services.prompts import get_analytics_prompt
import json

router = APIRouter(tags=["Analytics"])

class QuizRecord(BaseModel):
    title: str = Field(..., example="Quiz 1", description="The title of the quiz")
    topic: str = Field(..., example="Arrays", description="The subject/topic of the quiz")
    score: int = Field(..., example=40, description="The score percentage the student obtained")

class AnalyticsRequest(BaseModel):
    quizzes: List[QuizRecord] = Field(..., description="List of the student's historical quiz records")

class AnalyticsResponse(BaseModel):
    weak_topics: List[str] = Field(..., description="Topics where the student performed poorly")
    strong_topics: List[str] = Field(..., description="Topics where the student performed well")

@router.post("/analyze", response_model=AnalyticsResponse)
def analyze_student_performance(request: AnalyticsRequest):
    try:
        # Convert Pydantic models to dict list for prompt generation
        quiz_list = [q.model_dump() for q in request.quizzes]
        prompt = get_analytics_prompt(quiz_list)
        raw_response = generate_text(prompt, json_mode=True, response_schema=AnalyticsResponse)
        
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response.split("```json", 1)[1]
        if clean_response.endswith("```"):
            clean_response = clean_response.rsplit("```", 1)[0]
        clean_response = clean_response.strip()
        
        data = json.loads(clean_response)
        return AnalyticsResponse(**data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse Gemini response as JSON. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
