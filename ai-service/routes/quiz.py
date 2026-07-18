from fastapi import APIRouter, HTTPException
from typing import List, Literal
from pydantic import BaseModel, Field, field_validator
import json
from services.gemini import generate_text
from services.prompts import get_quiz_prompt
from utils.response import UnifiedResponse

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
    difficulty: Literal["Easy", "Medium", "Hard"] = Field("Easy", description="Difficulty level (Easy, Medium, Hard)")
    questions: int = Field(5, ge=1, le=10, description="Number of questions to generate (1 to 10)")

    @field_validator("topic")
    @classmethod
    def topic_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Topic cannot be empty or whitespace")
        return v.strip()

from utils.logger import get_logger

logger = get_logger("QuizRoute")

@router.post("/generate-quiz", response_model=UnifiedResponse[QuizResponse])
def generate_quiz(request: QuizRequest):
    logger.info(f"Incoming POST /generate-quiz request for topic: '{request.topic}', difficulty: '{request.difficulty}', questions: {request.questions}")
    try:
        prompt = get_quiz_prompt(request.topic, request.difficulty, request.questions)
        raw_response = generate_text(prompt, json_mode=True, response_schema=QuizResponse)
        
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response.split("```json", 1)[1]
        if clean_response.endswith("```"):
            clean_response = clean_response.rsplit("```", 1)[0]
        clean_response = clean_response.strip()
        
        try:
            quiz_data = json.loads(clean_response)
        except json.JSONDecodeError as jde:
            logger.error(f"JSON parsing failure in generate_quiz. Raw output: '{clean_response}'. Error: {str(jde)}")
            raise jde
            
        data = QuizResponse(**quiz_data)
        logger.info("Successfully generated quiz.")
        return UnifiedResponse(success=True, data=data)
    except Exception as e:
        logger.warning(f"Error in generate_quiz, falling back. Error: {str(e)}")
        # Graceful fallback: return a default quiz item
        fallback_item = QuizItem(
            question=f"Which of the following is a primary characteristic of '{request.topic}'?",
            options=[
                "It is a core concept in software engineering.",
                "It is completely unrelated to programming.",
                "It is only used in legacy hardware systems.",
                "None of the above."
            ],
            answer="A",
            explanation=f"This is a placeholder question generated because the AI tutor service is currently offline. Please try again later. (Error: {str(e)})"
        )
        data = QuizResponse(quiz=[fallback_item])
        return UnifiedResponse(success=True, data=data)
