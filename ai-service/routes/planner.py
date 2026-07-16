from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
from services.gemini import generate_text
from services.prompts import get_roadmap_prompt
import json

router = APIRouter(tags=["Study Planner"])

class PlannerRequest(BaseModel):
    exam: str = Field(..., example="JEE", description="The target exam")
    days_left: int = Field(..., example=30, description="Number of days left for the exam")
    subjects: List[str] = Field(..., example=["Physics", "Chemistry", "Math"], description="List of subjects to cover")
    daily_hours: int = Field(..., example=6, description="Daily study hours allocated")

class PlannerResponse(BaseModel):
    plan: Dict[str, List[str]] = Field(..., description="Day-by-day study roadmap")

@router.post("/roadmap", response_model=PlannerResponse)
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
        return PlannerResponse(**data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse Gemini response as JSON. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
