from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict
from services.gemini import generate_text
from services.prompts import get_roadmap_prompt
from utils.response import UnifiedResponse
import json

router = APIRouter(tags=["Study Planner"])

class PlannerRequest(BaseModel):
    exam: str = Field(..., example="JEE", description="The target exam")
    days_left: int = Field(..., example=30, gt=0, description="Number of days left for the exam (must be positive)")
    subjects: List[str] = Field(..., example=["Physics", "Chemistry", "Math"], description="List of subjects to cover")
    daily_hours: int = Field(..., example=6, ge=1, le=24, description="Daily study hours allocated (1 to 24)")

    @field_validator("exam")
    @classmethod
    def exam_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Exam name cannot be empty or whitespace")
        return v.strip()

    @field_validator("subjects")
    @classmethod
    def subjects_must_not_be_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Subjects list cannot be empty")
        cleaned = [s.strip() for s in v if s and s.strip()]
        if not cleaned:
            raise ValueError("Subjects list must contain at least one valid subject name")
        return cleaned

class PlannerResponse(BaseModel):
    plan: Dict[str, List[str]] = Field(..., description="Day-by-day study roadmap")

@router.post("/roadmap", response_model=UnifiedResponse[PlannerResponse])
def get_roadmap(request: PlannerRequest):
    try:
        prompt = get_roadmap_prompt(request.exam, request.days_left, request.subjects, request.daily_hours)
        raw_response = generate_text(prompt, json_mode=True, response_schema=PlannerResponse)
        
        # Clean response string in case Gemini still added markdown wrappers
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response.split("```json", 1)[1]
        if clean_response.endswith("```"):
            clean_response = clean_response.rsplit("```", 1)[0]
        clean_response = clean_response.strip()
        
        data = json.loads(clean_response)
        data_model = PlannerResponse(**data)
        return UnifiedResponse(success=True, data=data_model)
    except Exception as e:
        # Graceful fallback: generate a simple round-robin plan for the days
        fallback_plan = {}
        subjects_count = len(request.subjects)
        for day in range(1, request.days_left + 1):
            # Select subject for the day
            primary_subject = request.subjects[(day - 1) % subjects_count]
            secondary_subject = request.subjects[day % subjects_count]
            
            # Divide daily hours
            primary_hours = max(1, request.daily_hours - 2)
            secondary_hours = max(1, request.daily_hours - primary_hours)
            
            fallback_plan[f"Day {day}"] = [
                f"{primary_subject}: Study core topics and practice questions ({primary_hours} hours)",
                f"{secondary_subject}: Solve revision and textbook exercises ({secondary_hours} hours)",
                f"Review and self-assessment test (Fallback plan generated due to offline AI service: {str(e)[:50]}...)"
            ]
            
        data_model = PlannerResponse(plan=fallback_plan)
        return UnifiedResponse(success=True, data=data_model)
