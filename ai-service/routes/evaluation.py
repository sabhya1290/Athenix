from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from services.gemini import generate_text
from services.prompts import get_evaluation_prompt
import json

router = APIRouter(tags=["Evaluation"])

class EvaluationRequest(BaseModel):
    question: str = Field(..., example="Explain Binary Search", description="The question being answered")
    student_answer: str = Field(..., example="Binary Search divides the array...", description="The student's written answer")

    @field_validator("question", "student_answer")
    @classmethod
    def fields_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Input field cannot be empty or whitespace")
        return v.strip()

class EvaluationResponse(BaseModel):
    score: int = Field(..., description="The score evaluated out of 10")
    feedback: str = Field(..., description="Detailed feedback on the answer")
    improvement: str = Field(..., description="Areas/ways the student can improve their score")

from utils.response import UnifiedResponse

from utils.logger import get_logger

logger = get_logger("EvaluationRoute")

@router.post("/evaluate", response_model=UnifiedResponse[EvaluationResponse])
def evaluate_student_answer(request: EvaluationRequest):
    logger.info(f"Incoming POST /evaluate request for question: '{request.question[:50]}...'")
    try:
        prompt = get_evaluation_prompt(request.question, request.student_answer)
        raw_response = generate_text(prompt, json_mode=True, response_schema=EvaluationResponse)
        
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response.split("```json", 1)[1]
        if clean_response.endswith("```"):
            clean_response = clean_response.rsplit("```", 1)[0]
        clean_response = clean_response.strip()
        
        try:
            data = json.loads(clean_response)
        except json.JSONDecodeError as jde:
            logger.error(f"JSON parsing failure in evaluate_student_answer. Raw output: '{clean_response}'. Error: {str(jde)}")
            raise jde
            
        data_model = EvaluationResponse(**data)
        logger.info("Successfully evaluated student answer.")
        return UnifiedResponse(success=True, data=data_model)
    except Exception as e:
        logger.warning(f"Error in evaluate_student_answer, falling back. Error: {str(e)}")
        fallback_data = EvaluationResponse(
            score=5,
            feedback=f"We were temporarily unable to reach the AI evaluator. Your answer has been saved. Please try again later. (Error: {str(e)[:50]}...)",
            improvement="Ensure your answer fully addresses all parts of the question, provides examples, and uses clear technical definitions."
        )
        return UnifiedResponse(success=True, data=fallback_data)
