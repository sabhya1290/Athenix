# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Dict
from services.gemini import generate_text
from services.prompts import get_recommendation_prompt
import json

router = APIRouter(tags=["Recommendation"])

class RecommendationRequest(BaseModel):
    scores: Dict[str, int] = Field(
        ...,
        example={"Math": 80, "Physics": 32, "Chemistry": 65},
        description="Dictionary mapping subjects to their corresponding percentage score"
    )

class RecommendationResponse(BaseModel):
    recommendation: str = Field(..., description="Personalized recommendation and study plan text")

from utils.response import UnifiedResponse

@router.post("/recommend", response_model=UnifiedResponse[RecommendationResponse])
def get_recommendation(request: RecommendationRequest):
    try:
        prompt = get_recommendation_prompt(request.scores)
        raw_response = generate_text(prompt, json_mode=True, response_schema=RecommendationResponse)
        
        # Clean response string in case Gemini still added markdown wrappers
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response.split("```json", 1)[1]
        if clean_response.endswith("```"):
            clean_response = clean_response.rsplit("```", 1)[0]
        clean_response = clean_response.strip()
        
        data = json.loads(clean_response)
        data_model = RecommendationResponse(**data)
        return UnifiedResponse(success=True, data=data_model)
    except json.JSONDecodeError:
        return UnifiedResponse(success=False, error="Failed to parse Gemini response as JSON. Please try again.")
    except Exception as e:
        return UnifiedResponse(success=False, error=str(e))
