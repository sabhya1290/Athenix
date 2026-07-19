from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal
from services.gemini import generate_text
from services.prompts import get_skill_gap_prompt
from routes.analytics import QuizRecord, AnalyticsRequest
from utils.response import UnifiedResponse
from utils.logger import get_logger
import json

logger = get_logger("SkillGapRoute")
router = APIRouter(tags=["Skill Gap Detection"])

class SkillGapItem(BaseModel):
    topic: str = Field(..., description="The topic with a detected skill gap")
    reason: str = Field(..., description="Detailed diagnosis of the student's gaps and errors")
    priority: Literal["High", "Medium", "Low"] = Field(..., description="Priority level for fixing the gap")
    gaps_resources: List[str] = Field(..., description="Suggested study material, resources, or links")

class SkillGapResponse(BaseModel):
    gaps: List[SkillGapItem] = Field(..., description="List of detected skill gaps")

@router.post("/skill-gap", response_model=UnifiedResponse[SkillGapResponse])
def detect_skill_gap(request: AnalyticsRequest):
    logger.info(f"Incoming POST /skill-gap request with {len(request.quizzes)} quiz records")
    try:
        quiz_list = [q.model_dump() for q in request.quizzes]
        prompt = get_skill_gap_prompt(quiz_list)
        raw_response = generate_text(prompt, json_mode=True, response_schema=SkillGapResponse)
        
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
            logger.error(f"JSON parsing failure in detect_skill_gap. Raw output: '{clean_response}'. Error: {str(jde)}")
            raise jde
            
        data_model = SkillGapResponse(**data)
        logger.info("Successfully completed Skill Gap Detection.")
        return UnifiedResponse(success=True, data=data_model)
    except Exception as e:
        logger.warning(f"Error in detect_skill_gap, falling back. Error: {str(e)}")
        # Program local fallback metrics
        gaps_list = []
        topic_scores = {}
        for q in request.quizzes:
            if q.topic not in topic_scores:
                topic_scores[q.topic] = []
            topic_scores[q.topic].append(q.score)
            
        for topic, scores in topic_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 70:
                priority = "High" if avg_score < 50 else "Medium"
                
                # Dynamic fallback reason
                reason = (
                    f"Student scored an average of {round(avg_score, 1)}% in historical quizzes. "
                    f"Struggles to complete questions accurately under timed pressure."
                )
                
                # Standard fallback educational resources mapping
                gaps_resources = [
                    f"NCERT textbook chapter review on {topic}",
                    f"Khan Academy tutorial videos on {topic}",
                    f"Solve 20 practice questions of Easy/Medium difficulty on {topic}"
                ]
                
                gaps_list.append(SkillGapItem(
                    topic=topic,
                    reason=reason,
                    priority=priority,
                    gaps_resources=gaps_resources
                ))
                
        # If no gaps calculated locally, output a default general review recommendation
        if not gaps_list and request.quizzes:
            gaps_list.append(SkillGapItem(
                topic=request.quizzes[0].topic,
                reason="General review and consolidation recommended to maintain scores.",
                priority="Low",
                gaps_resources=["General past year question papers"]
            ))
            
        fallback_data = SkillGapResponse(gaps=gaps_list)
        return UnifiedResponse(success=True, data=fallback_data)
