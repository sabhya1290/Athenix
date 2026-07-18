# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, field_validator
from typing import Dict
from services.gemini import generate_text
from services.prompts import get_recommendation_prompt
from utils.response import UnifiedResponse
import json

router = APIRouter(tags=["Recommendation"])

class RecommendationRequest(BaseModel):
    scores: Dict[str, int] = Field(
        ...,
        example={"Math": 80, "Physics": 32, "Chemistry": 65},
        description="Dictionary mapping subjects to their corresponding percentage score"
    )

    @field_validator("scores")
    @classmethod
    def validate_scores(cls, v: Dict[str, int]) -> Dict[str, int]:
        if not v:
            raise ValueError("Scores dictionary cannot be empty")
        for subject, score in v.items():
            if not subject or not subject.strip():
                raise ValueError("Subject name cannot be empty or whitespace")
            if not (0 <= score <= 100):
                raise ValueError(f"Score for '{subject}' must be between 0 and 100")
        return v

class RecommendationResponse(BaseModel):
    recommendation: str = Field(..., description="Personalized recommendation and study plan text")

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
    except Exception as e:
        # Determine the weakest subject based on scores
        weakest_subject = min(request.scores, key=request.scores.get)
        weakest_score = request.scores[weakest_subject]
        
        fallback_msg = (
            f"The AI recommendation engine is currently offline, but we've analyzed your scores locally. "
            f"Your lowest score is in '{weakest_subject}' ({weakest_score}%). We recommend allocating 60% of your "
            f"study time today to review '{weakest_subject}', 30% to your next lowest subject, and 10% to review "
            f"and maintain your strongest subjects. You've got this! (Error: {str(e)})"
        )
        data_model = RecommendationResponse(recommendation=fallback_msg)
        return UnifiedResponse(success=True, data=data_model)
