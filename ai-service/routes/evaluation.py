from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.gemini import generate_text
from services.prompts import get_evaluation_prompt
import json

router = APIRouter(tags=["Evaluation"])

class EvaluationRequest(BaseModel):
    question: str = Field(..., example="Explain Binary Search", description="The question being answered")
    student_answer: str = Field(..., example="Binary Search divides the array...", description="The student's written answer")

class EvaluationResponse(BaseModel):
    score: int = Field(..., description="The score evaluated out of 10")
    feedback: str = Field(..., description="Detailed feedback on the answer")
    improvement: str = Field(..., description="Areas/ways the student can improve their score")

from utils.response import UnifiedResponse

@router.post("/evaluate", response_model=UnifiedResponse[EvaluationResponse])
def evaluate_student_answer(request: EvaluationRequest):
    try:
        prompt = get_evaluation_prompt(request.question, request.student_answer)
        raw_response = generate_text(prompt, json_mode=True, response_schema=EvaluationResponse)
        
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response.split("```json", 1)[1]
        if clean_response.endswith("```"):
            clean_response = clean_response.rsplit("```", 1)[0]
        clean_response = clean_response.strip()
        
        data = json.loads(clean_response)
        data_model = EvaluationResponse(**data)
        return UnifiedResponse(success=True, data=data_model)
    except json.JSONDecodeError:
        return UnifiedResponse(success=False, error="Failed to parse Gemini response as JSON. Please try again.")
    except Exception as e:
        return UnifiedResponse(success=False, error=str(e))
