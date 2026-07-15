from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
import json
from services.gemini import generate_text
from services.prompts import get_quiz_prompt

router = APIRouter(tags=["Quiz"])

class QuizItem(BaseModel):
    question: str = Field(..., description="The multiple choice question")
    options: List[str] = Field(..., description="List of 4 choices/options")
    answer: str = Field(..., description="The correct option (A, B, C, or D)")
    explanation: str = Field(..., description="Short explanation of why the answer is correct")

class QuizResponse(BaseModel):
    quiz: List[QuizItem] = Field(..., description="List of quiz questions")

class QuizRequest(BaseModel):
    topic: str = Field(..., example="Arrays", description="The topic for the quiz")
    difficulty: str = Field("Easy", example="Easy", description="Difficulty level (Easy, Medium, Hard)")
    questions: int = Field(5, example=5, description="Number of questions to generate")

@router.post("/generate-quiz", response_model=QuizResponse)
def generate_quiz(request: QuizRequest):
    try:
        prompt = get_quiz_prompt(request.topic, request.difficulty, request.questions)
        # Request JSON mode from Gemini helper
        raw_response = generate_text(prompt, json_mode=True)
        
        # Clean response string in case Gemini still added markdown wrappers
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response.split("```json", 1)[1]
        if clean_response.endswith("```"):
            clean_response = clean_response.rsplit("```", 1)[0]
        clean_response = clean_response.strip()
        
        quiz_data = json.loads(clean_response)
        return QuizResponse(**quiz_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse Gemini response as JSON. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
