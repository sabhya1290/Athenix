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

from typing import List, Literal

class WeakTopicDetail(BaseModel):
    topic: str = Field(..., example="Arrays", description="The weak topic/concept name")
    importance: Literal["High", "Medium", "Low"] = Field("Medium", example="High", description="Importance of the topic for the course")
    exam_weightage: str = Field(..., example="12%", description="Weightage in the exam (e.g. '12%' or 'High')")
    past_mistakes_count: int = Field(..., ge=0, example=4, description="Number of past mistakes on this topic")

class RecommendationRequest(BaseModel):
    subjects: List[str] = Field(..., example=["Math", "Physics", "Chemistry"], description="List of subjects the student is taking")
    weak_topics: List[WeakTopicDetail] = Field(..., description="Detailed breakdown of the student's weak topics")
    strong_topics: List[str] = Field(..., example=["Mechanics", "Organic Chemistry"], description="List of strong topics/concepts")
    average_score: float = Field(..., ge=0, le=100, example=65.5, description="Average score across recent quizzes")
    learning_pace: Literal["Slow", "Medium", "Fast"] = Field("Medium", example="Medium", description="The student's learning speed")
    study_hours: int = Field(..., ge=1, le=24, example=6, description="Allocated daily study hours")
    consistency: Literal["High", "Medium", "Low"] = Field("Medium", example="High", description="Student's study consistency level")
    last_studied: str = Field(..., example="2026-07-18", description="Last study session date")
    preferred_difficulty: Literal["Easy", "Medium", "Hard"] = Field("Medium", example="Medium", description="Preferred study material difficulty")
    days_left: int = Field(..., gt=0, example=30, description="Number of days left until the exam")

    @field_validator("subjects")
    @classmethod
    def validate_subjects(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Subjects list cannot be empty")
        cleaned = [s.strip() for s in v if s and s.strip()]
        if not cleaned:
            raise ValueError("Subjects list must contain at least one valid subject name")
        return cleaned

class RecommendationResponse(BaseModel):
    recommendation: str = Field(..., description="Personalized recommendation and study plan text")

from utils.logger import get_logger

logger = get_logger("RecommendationRoute")

@router.post("/recommend", response_model=UnifiedResponse[RecommendationResponse])
def get_recommendation(request: RecommendationRequest):
    logger.info(f"Incoming POST /recommend request for profile with average score: {request.average_score}%")
    try:
        # Pass the whole request as a dict to prompt template
        profile_dict = request.model_dump()
        prompt = get_recommendation_prompt(profile_dict)
        raw_response = generate_text(prompt, json_mode=True, response_schema=RecommendationResponse)
        
        # Clean response string in case Gemini still added markdown wrappers
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response.split("```json", 1)[1]
        if clean_response.endswith("```"):
            clean_response = clean_response.rsplit("```", 1)[0]
        clean_response = clean_response.strip()
        
        try:
            data = json.loads(clean_response)
        except json.JSONDecodeError as jde:
            logger.error(f"JSON parsing failure in get_recommendation. Raw output: '{clean_response}'. Error: {str(jde)}")
            raise jde
            
        data_model = RecommendationResponse(**data)
        logger.info("Successfully generated study recommendations based on student profile.")
        return UnifiedResponse(success=True, data=data_model)
    except Exception as e:
        logger.warning(f"Error in get_recommendation, falling back. Error: {str(e)}")
        # Heuristic local sorting for fallback: prioritize by mistakes * weightage (High=3, Med=2, Low=1)
        importance_map = {"High": 3, "Medium": 2, "Low": 1}
        sorted_weak = sorted(
            request.weak_topics,
            key=lambda x: x.past_mistakes_count * importance_map.get(x.importance, 2),
            reverse=True
        )
        
        weak_priority_text = ""
        if sorted_weak:
            top_weak = sorted_weak[0]
            weak_priority_text = f"We highly recommend prioritizing '{top_weak.topic}' (which has {top_weak.past_mistakes_count} past mistakes and holds {top_weak.importance} importance). "
            
        fallback_msg = (
            f"The AI recommendation engine is currently offline, but we've analyzed your learning profile locally. "
            f"{weak_priority_text}"
            f"Given you have {request.days_left} days left and study {request.study_hours} hours daily at a '{request.learning_pace}' pace, "
            f"allocate 70% of today's time to your highest-error topics using '{request.preferred_difficulty}' difficulty questions. (Error: {str(e)[:50]}...)"
        )
        data_model = RecommendationResponse(recommendation=fallback_msg)
        return UnifiedResponse(success=True, data=data_model)
