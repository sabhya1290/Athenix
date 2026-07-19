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

class WeaknessPriorityItem(BaseModel):
    topic: str = Field(..., description="The name of the weak topic")
    calculated_priority_score: int = Field(..., description="Calculated priority score (0-100) based on importance, weightage, and errors")
    priority_level: Literal["Critical", "High", "Medium", "Low"] = Field(..., description="Priority tier")
    actionable_plan: str = Field(..., description="Actionable recommendation block")

class RecommendationResponse(BaseModel):
    weakness_priorities: List[WeaknessPriorityItem] = Field(..., description="Topic-wise priority list")
    daily_allocated_hours: Dict[str, float] = Field(..., description="Suggested daily study hours allocation")
    exam_readiness_outlook: str = Field(..., description="AI evaluation of target exam readiness and timeline")
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
        # Algorithm-based local calculation for recommendation:
        importance_map = {"High": 3, "Medium": 2, "Low": 1}
        weak_priorities = []
        daily_allocations = {}
        
        # Distribute study hours among weak topics
        total_study_hours = request.study_hours
        remaining_hours = total_study_hours
        
        sorted_weak = sorted(
            request.weak_topics,
            key=lambda x: x.past_mistakes_count * importance_map.get(x.importance, 2),
            reverse=True
        )
        
        for idx, wt in enumerate(sorted_weak):
            # Calculate a priority score out of 100
            base_score = wt.past_mistakes_count * 15
            importance_weight = importance_map.get(wt.importance, 2) * 10
            calculated_priority = min(100, base_score + importance_weight)
            
            if calculated_priority >= 75:
                level = "Critical"
            elif calculated_priority >= 50:
                level = "High"
            elif calculated_priority >= 30:
                level = "Medium"
            else:
                level = "Low"
                
            # Distribute daily hours: give more hours to higher priority
            allocated = 0.0
            if remaining_hours > 0:
                if idx == 0:
                    allocated = round(total_study_hours * 0.6, 1)
                elif idx == 1:
                    allocated = round(total_study_hours * 0.3, 1)
                else:
                    allocated = round(remaining_hours, 1)
                allocated = min(allocated, remaining_hours)
                remaining_hours = round(remaining_hours - allocated, 1)
                
            daily_allocations[wt.topic] = allocated
            
            actionable_plan = (
                f"Allocate {allocated} daily hours to master '{wt.topic}'. "
                f"Focus on resolving past mistakes ({wt.past_mistakes_count} errors logged) via custom practice papers."
            )
            
            weak_priorities.append(WeaknessPriorityItem(
                topic=wt.topic,
                calculated_priority_score=calculated_priority,
                priority_level=level,
                actionable_plan=actionable_plan
            ))
            
        outlook = (
            f"Exam is in {request.days_left} days. Based on the local analysis, "
            f"the student has critical weak points that require focused daily practice. "
            f"Readiness outlook: Medium."
        )
        
        recommendation_text = (
            f"Locally calculated recommendations are active. Prioritize weak topics based on past mistakes count. "
            f"Daily study budget is {request.study_hours} hours. Please check the weakness priorities list."
        )
        
        fallback_data = RecommendationResponse(
            weakness_priorities=weak_priorities,
            daily_allocated_hours=daily_allocations,
            exam_readiness_outlook=outlook,
            recommendation=recommendation_text
        )
        return UnifiedResponse(success=True, data=fallback_data)
