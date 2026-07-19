from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from services.profile_store import get_profile, upsert_profile, ingest_quiz_record, list_student_ids
from utils.response import UnifiedResponse
from utils.logger import get_logger

logger = get_logger("ProfileRoute")
router = APIRouter(prefix="/profile", tags=["Learning Profile"])


class QuizIngestionRecord(BaseModel):
    title: str = Field(..., example="Math Quiz 1")
    topic: str = Field(..., example="Calculus")
    score: int = Field(..., ge=0, le=100, example=72)
    completion_time_seconds: int = Field(default=60, example=120)
    correct_answers: int = Field(default=7, example=7)
    total_questions: int = Field(default=10, example=10)
    difficulty: Literal["Easy", "Medium", "Hard"] = Field(default="Medium")
    completed_at: Optional[str] = Field(None, example="2024-07-19T10:00:00Z")


class ProfileUpdateRequest(BaseModel):
    study_hours: Optional[int] = Field(None, example=5)
    preferred_difficulty: Optional[Literal["Easy", "Medium", "Hard"]] = Field(None)
    last_activity: Optional[str] = Field(None)


class ProfileResponse(BaseModel):
    student_id: str
    weak_topics: List[str]
    strong_topics: List[str]
    average_score: float
    study_hours: int
    learning_pace: str
    consistency: str
    preferred_difficulty: str
    last_activity: Optional[str]
    quiz_history_count: int
    mentor_session_count: int
    has_performance_snapshot: bool


class IngestQuizRequest(BaseModel):
    quizzes: List[QuizIngestionRecord] = Field(..., description="One or more quiz records to ingest")


@router.get("/{student_id}", response_model=UnifiedResponse[ProfileResponse])
def get_student_profile(student_id: str):
    """Fetch the current learning profile for a student."""
    logger.info(f"GET /profile/{student_id}")
    profile = get_profile(student_id)
    data = ProfileResponse(
        student_id=profile["student_id"],
        weak_topics=profile["weak_topics"],
        strong_topics=profile["strong_topics"],
        average_score=profile["average_score"],
        study_hours=profile["study_hours"],
        learning_pace=profile["learning_pace"],
        consistency=profile["consistency"],
        preferred_difficulty=profile["preferred_difficulty"],
        last_activity=profile.get("last_activity"),
        quiz_history_count=len(profile.get("quiz_history", [])),
        mentor_session_count=len(profile.get("mentor_session_memory", [])),
        has_performance_snapshot=profile.get("performance_snapshot") is not None,
    )
    return UnifiedResponse(success=True, data=data)


@router.post("/{student_id}/ingest", response_model=UnifiedResponse[ProfileResponse])
def ingest_quiz_records(student_id: str, request: IngestQuizRequest):
    """
    Ingest quiz results into the student's profile.
    Automatically recomputes weak/strong topics, learning pace, consistency,
    and preferred difficulty based on all historical quiz data.
    """
    logger.info(f"POST /profile/{student_id}/ingest — {len(request.quizzes)} record(s)")
    for quiz in request.quizzes:
        ingest_quiz_record(student_id, quiz.model_dump())

    profile = get_profile(student_id)
    data = ProfileResponse(
        student_id=profile["student_id"],
        weak_topics=profile["weak_topics"],
        strong_topics=profile["strong_topics"],
        average_score=profile["average_score"],
        study_hours=profile["study_hours"],
        learning_pace=profile["learning_pace"],
        consistency=profile["consistency"],
        preferred_difficulty=profile["preferred_difficulty"],
        last_activity=profile.get("last_activity"),
        quiz_history_count=len(profile.get("quiz_history", [])),
        mentor_session_count=len(profile.get("mentor_session_memory", [])),
        has_performance_snapshot=profile.get("performance_snapshot") is not None,
    )
    return UnifiedResponse(success=True, data=data)


@router.patch("/{student_id}", response_model=UnifiedResponse[ProfileResponse])
def update_student_profile(student_id: str, request: ProfileUpdateRequest):
    """Manually update editable fields of a student's profile (e.g. study_hours, difficulty preference)."""
    logger.info(f"PATCH /profile/{student_id}")
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    profile = upsert_profile(student_id, updates)
    data = ProfileResponse(
        student_id=profile["student_id"],
        weak_topics=profile["weak_topics"],
        strong_topics=profile["strong_topics"],
        average_score=profile["average_score"],
        study_hours=profile["study_hours"],
        learning_pace=profile["learning_pace"],
        consistency=profile["consistency"],
        preferred_difficulty=profile["preferred_difficulty"],
        last_activity=profile.get("last_activity"),
        quiz_history_count=len(profile.get("quiz_history", [])),
        mentor_session_count=len(profile.get("mentor_session_memory", [])),
        has_performance_snapshot=profile.get("performance_snapshot") is not None,
    )
    return UnifiedResponse(success=True, data=data)


@router.get("/", response_model=UnifiedResponse[List[str]])
def list_profiles():
    """List all student IDs with active profiles."""
    return UnifiedResponse(success=True, data=list_student_ids())
