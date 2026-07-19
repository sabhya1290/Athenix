from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from services.gemini import generate_text
from services.prompts import get_performance_prediction_prompt
from services.profile_store import get_profile, set_performance_snapshot
from routes.analytics import QuizRecord
from utils.response import UnifiedResponse
from utils.logger import get_logger
import json

logger = get_logger("PredictRoute")
router = APIRouter(tags=["Performance Prediction"])


class PredictRequest(BaseModel):
    quizzes: List[QuizRecord] = Field(..., description="Historical quiz records for prediction")
    student_id: Optional[str] = Field(None, description="Optional student ID to auto-load profile data")
    exam: Optional[str] = Field("JEE", example="JEE", description="Target exam name")
    days_left: Optional[int] = Field(30, example=30, description="Days remaining until the exam")


class PredictResponse(BaseModel):
    current_readiness_pct: float = Field(..., description="Current exam readiness percentage (0-100)")
    expected_score: int = Field(..., description="Expected exam score (scale of 300)")
    probability_of_clearing: Literal["High", "Medium", "Low"] = Field(..., description="Probability of clearing the exam")
    critical_weak_topic: str = Field(..., description="The single most critical topic to focus on right now")
    readiness_breakdown: dict = Field(..., description="Subject-level readiness breakdown")
    improvement_actions: List[str] = Field(..., description="Top 3 concrete actions to improve score")
    predicted_rank: str = Field(..., description="Predicted rank range in the exam")
    confidence_message: str = Field(..., description="Encouraging or cautionary message based on readiness")


@router.post("/predict", response_model=UnifiedResponse[PredictResponse])
def predict_performance(request: PredictRequest):
    """
    Predict student's exam performance based on quiz history.
    Optionally merges stored learning profile data for richer predictions.
    Returns: readiness %, expected score, probability of clearing, critical topic, rank, actions.
    """
    logger.info(f"POST /predict — {len(request.quizzes)} quizzes, exam={request.exam}, days_left={request.days_left}")

    # Load profile data if student_id provided
    profile_context = {}
    if request.student_id:
        profile = get_profile(request.student_id)
        profile_context = {
            "learning_pace": profile.get("learning_pace", "Normal learner"),
            "consistency": profile.get("consistency", "Medium"),
            "study_hours": profile.get("study_hours", 2),
            "mentor_sessions": len(profile.get("mentor_session_memory", [])),
        }

    quiz_list = [q.model_dump() for q in request.quizzes]

    try:
        prompt = get_performance_prediction_prompt(
            quizzes=quiz_list,
            exam=request.exam,
            days_left=request.days_left,
            profile_context=profile_context
        )
        raw = generate_text(prompt, json_mode=True, response_schema=PredictResponse)
        clean = raw.strip()
        if clean.startswith("```json"):
            clean = clean.split("```json", 1)[1]
        if clean.endswith("```"):
            clean = clean.rsplit("```", 1)[0]
        clean = clean.strip()

        data_dict = json.loads(clean)
        data = PredictResponse(**data_dict)
        logger.info("Successfully generated performance prediction.")

        # Cache snapshot in profile
        if request.student_id:
            set_performance_snapshot(request.student_id, data_dict)

        return UnifiedResponse(success=True, data=data)

    except Exception as e:
        logger.warning(f"Gemini prediction failed, using heuristics. Error: {str(e)}")

        # --- Local heuristic fallback ---
        topic_scores: dict = {}
        for q in request.quizzes:
            if q.topic not in topic_scores:
                topic_scores[q.topic] = []
            topic_scores[q.topic].append(q.score)

        all_scores = [q.score for q in request.quizzes]
        avg = sum(all_scores) / len(all_scores) if all_scores else 0

        # Per-subject readiness
        readiness_breakdown = {
            topic: round(sum(scores) / len(scores), 1)
            for topic, scores in topic_scores.items()
        }

        # Most critical weak topic
        sorted_topics = sorted(topic_scores.items(), key=lambda x: sum(x[1]) / len(x[1]))
        critical_topic = sorted_topics[0][0] if sorted_topics else "Unknown"

        # Expected score (scale of 300)
        expected_score = int(avg * 3)

        # Probability and rank
        if avg >= 80:
            prob = "High"
            rank = "Top 5%"
        elif avg >= 60:
            prob = "Medium"
            rank = "Top 20%"
        else:
            prob = "Low"
            rank = "Top 50%"

        # Days-left adjusted readiness
        readiness = round(avg * 0.9 if request.days_left and request.days_left < 7 else avg, 1)

        # Improvement actions
        actions = [
            f"Focus intensive revision on '{critical_topic}' — your lowest scoring topic.",
            "Attempt at least 2 full-length mock tests this week to build exam stamina.",
            "Review all incorrect answers from past quizzes and understand the reasoning.",
        ]

        # Confidence message
        if avg >= 80:
            msg = "Excellent preparation! Stay consistent and avoid overconfidence."
        elif avg >= 60:
            msg = "You're on track. Address weak topics daily and you will clear the exam."
        else:
            msg = "You need focused effort. Prioritize your weakest topics and practice daily."

        fallback = PredictResponse(
            current_readiness_pct=readiness,
            expected_score=expected_score,
            probability_of_clearing=prob,
            critical_weak_topic=critical_topic,
            readiness_breakdown=readiness_breakdown,
            improvement_actions=actions,
            predicted_rank=rank,
            confidence_message=msg,
        )

        if request.student_id:
            set_performance_snapshot(request.student_id, fallback.model_dump())

        return UnifiedResponse(success=True, data=fallback)
