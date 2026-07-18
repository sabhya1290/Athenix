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

class AnalyticsResponse(BaseModel):
    weak_topics: List[str] = Field(..., description="Topics where the student performed poorly")
    strong_topics: List[str] = Field(..., description="Topics where the student performed well")

from utils.response import UnifiedResponse

@router.post("/analyze", response_model=UnifiedResponse[AnalyticsResponse])
def analyze_student_performance(request: AnalyticsRequest):
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
        
        data = json.loads(clean_response)
        data_model = AnalyticsResponse(**data)
        return UnifiedResponse(success=True, data=data_model)
    except Exception as e:
        # Graceful local fallback: calculate weak (< 60%) and strong (>= 75%) topics deterministically
        topic_scores = {}
        for q in request.quizzes:
            if q.topic not in topic_scores:
                topic_scores[q.topic] = []
            topic_scores[q.topic].append(q.score)
            
        weak_topics = []
        strong_topics = []
        
        for topic, scores in topic_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 60:
                weak_topics.append(topic)
            elif avg_score >= 75:
                strong_topics.append(topic)
                
        # Handle cases where all scores are in between 60 and 75
        if not weak_topics and not strong_topics:
            # Sort topics by average score to allocate at least one weak and one strong
            sorted_topics = sorted(topic_scores.keys(), key=lambda t: sum(topic_scores[t])/len(topic_scores[t]))
            if sorted_topics:
                weak_topics.append(sorted_topics[0])
                strong_topics.append(sorted_topics[-1])
                
        # Deduplicate
        weak_topics = list(set(weak_topics))
        strong_topics = list(set(strong_topics))
        
        fallback_data = AnalyticsResponse(
            weak_topics=weak_topics,
            strong_topics=strong_topics
        )
        return UnifiedResponse(success=True, data=fallback_data)
