from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List
from services.gemini import generate_text
from services.prompts import get_analytics_prompt
import json

router = APIRouter(tags=["Analytics"])

class QuizRecord(BaseModel):
    title: str = Field(..., example="Quiz 1", description="The title of the quiz")
    topic: str = Field(..., example="Arrays", description="The subject/topic of the quiz")
    score: int = Field(..., example=40, description="The score percentage the student obtained")

    @field_validator("title", "topic")
    @classmethod
    def fields_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Quiz fields cannot be empty or whitespace")
        return v.strip()

    @field_validator("score")
    @classmethod
    def score_must_be_percentage(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100")
        return v

class AnalyticsRequest(BaseModel):
    quizzes: List[QuizRecord] = Field(..., description="List of the student's historical quiz records")

    @field_validator("quizzes")
    @classmethod
    def quizzes_must_not_be_empty(cls, v: List[QuizRecord]) -> List[QuizRecord]:
        if not v:
            raise ValueError("Quizzes list cannot be empty")
        return v

from typing import Dict

class AnalyticsResponse(BaseModel):
    weak_topics: List[str] = Field(..., description="Topics where the student performed poorly")
    strong_topics: List[str] = Field(..., description="Topics where the student performed well")
    topic_mastery: Dict[str, float] = Field(..., description="Percentage mastery of each topic")
    weakness_graph: Dict[str, float] = Field(..., description="Calculated weakness intensity/error rates for weak topics")
    learning_trend: str = Field(..., description="Trend indication (e.g. Improving, Stable, Declining)")
    improvement_pct: float = Field(..., description="Improvement percentage rate")
    confidence_score: float = Field(..., description="Estimated student confidence score out of 100")
    accuracy_by_subject: Dict[str, float] = Field(..., description="Accuracy percentage by subject/topic category")
    time_spent: Dict[str, int] = Field(..., description="Estimated study time spent in minutes per category/subject")
    predicted_rank: str = Field(..., description="AI predicted rank range")
    predicted_exam_readiness: float = Field(..., description="AI predicted exam readiness percentage")

from utils.response import UnifiedResponse
from utils.logger import get_logger

logger = get_logger("AnalyticsRoute")

@router.post("/analyze", response_model=UnifiedResponse[AnalyticsResponse])
def analyze_student_performance(request: AnalyticsRequest):
    logger.info(f"Incoming POST /analyze request with {len(request.quizzes)} quiz records")
    try:
        # Convert Pydantic models to dict list for prompt generation
        quiz_list = [q.model_dump() for q in request.quizzes]
        prompt = get_analytics_prompt(quiz_list)
        raw_response = generate_text(prompt, json_mode=True, response_schema=AnalyticsResponse)
        
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response.split("```json", 1)[1]
        if clean_response.endswith("```"):
            clean_response = clean_response.rsplit("```", 1)[0]
        clean_response = clean_response.strip()
        
        try:
            data = json.loads(clean_response)
        except json.JSONDecodeError as jde:
            logger.error(f"JSON parsing failure in analyze_student_performance. Raw output: '{clean_response}'. Error: {str(jde)}")
            raise jde
            
        data_model = AnalyticsResponse(**data)
        logger.info("Successfully analyzed performance.")
        return UnifiedResponse(success=True, data=data_model)
    except Exception as e:
        logger.warning(f"Error in analyze_student_performance, falling back. Error: {str(e)}")
        # Calculate local fallback metrics
        topic_scores = {}
        for q in request.quizzes:
            if q.topic not in topic_scores:
                topic_scores[q.topic] = []
            topic_scores[q.topic].append(q.score)
            
        weak_topics = []
        strong_topics = []
        topic_mastery = {}
        weakness_graph = {}
        accuracy_by_subject = {}
        time_spent = {}
        
        for topic, scores in topic_scores.items():
            avg_score = sum(scores) / len(scores)
            topic_mastery[topic] = round(avg_score, 1)
            accuracy_by_subject[topic] = round(avg_score, 1)
            time_spent[topic] = len(scores) * 60  # Assume 60 minutes spent per quiz
            
            if avg_score < 60:
                weak_topics.append(topic)
                weakness_graph[topic] = round((100 - avg_score) / 100.0, 2)
            elif avg_score >= 75:
                strong_topics.append(topic)
                
        if not weak_topics and not strong_topics:
            sorted_topics = sorted(topic_scores.keys(), key=lambda t: sum(topic_scores[t])/len(topic_scores[t]))
            if sorted_topics:
                weak_topics.append(sorted_topics[0])
                weakness_graph[sorted_topics[0]] = round((100 - (sum(topic_scores[sorted_topics[0]])/len(topic_scores[sorted_topics[0]])))/100.0, 2)
                strong_topics.append(sorted_topics[-1])
                
        # Learning trend & improvement calculation
        all_scores = [q.score for q in request.quizzes]
        avg_score = sum(all_scores) / len(all_scores)
        
        trend = "Stable"
        improvement = 0.0
        if len(all_scores) >= 2:
            first_half = all_scores[:len(all_scores)//2]
            second_half = all_scores[len(all_scores)//2:]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            improvement = round(avg_second - avg_first, 1)
            if improvement > 5:
                trend = "Improving"
            elif improvement < -5:
                trend = "Declining"
                
        predicted_rank = "Top 50%"
        if avg_score >= 90:
            predicted_rank = "Top 1%"
        elif avg_score >= 80:
            predicted_rank = "Top 5%"
        elif avg_score >= 70:
            predicted_rank = "Top 15%"
            
        fallback_data = AnalyticsResponse(
            weak_topics=list(set(weak_topics)),
            strong_topics=list(set(strong_topics)),
            topic_mastery=topic_mastery,
            weakness_graph=weakness_graph,
            learning_trend=trend,
            improvement_pct=improvement,
            confidence_score=round(avg_score * 0.9, 1),
            accuracy_by_subject=accuracy_by_subject,
            time_spent=time_spent,
            predicted_rank=predicted_rank,
            predicted_exam_readiness=round(avg_score, 1)
        )
        return UnifiedResponse(success=True, data=fallback_data)
