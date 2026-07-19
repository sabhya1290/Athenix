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
    gap_analysis: str = Field(..., description="Detailed diagnosis of the student's gaps and errors")
    priority_ranking: Literal["High", "Medium", "Low"] = Field(..., description="Priority level for fixing the gap")
    recommended_action: str = Field(..., description="Actionable recommendation study actions")

from typing import Dict

class SkillGapResponse(BaseModel):
    topic_accuracies: Dict[str, float] = Field(..., description="Calculated accuracies by topic")
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
            
        topic_accuracies = {}
        for topic, scores in topic_scores.items():
            avg_score = sum(scores) / len(scores)
            topic_accuracies[topic] = round(avg_score, 1)
            
            if avg_score < 70:
                priority = "High" if avg_score < 50 else "Medium"
                
                # Dynamic fallback gap analysis
                analysis = (
                    f"Student scored an average of {round(avg_score, 1)}% in historical quizzes on {topic}. "
                    f"Conceptual gaps exist, combined with slow speed and low accuracy on medium/hard questions."
                )
                
                # Standard fallback educational resources mapping
                action = (
                    f"Review NCERT chapter for {topic}, solve 20 practice questions, and watch tutorial playlists."
                )
                
                gaps_list.append(SkillGapItem(
                    topic=topic,
                    gap_analysis=analysis,
                    priority_ranking=priority,
                    recommended_action=action
                ))
                
        # If no gaps calculated locally, output a default general review recommendation
        if not gaps_list and request.quizzes:
            gaps_list.append(SkillGapItem(
                topic=request.quizzes[0].topic,
                gap_analysis="Excellent general scores. No major gaps identified.",
                priority_ranking="Low",
                recommended_action="Solve mixed past-year exams to consolidate knowledge."
            ))
            
        fallback_data = SkillGapResponse(topic_accuracies=topic_accuracies, gaps=gaps_list)
        return UnifiedResponse(success=True, data=fallback_data)
