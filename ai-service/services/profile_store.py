"""
Learning Profile Store
======================
In-memory store for persistent student profiles.
Each student is identified by a student_id.
Profiles are updated incrementally as quizzes are submitted, 
and are read by every AI endpoint to personalize responses.
"""

from typing import Dict, List, Optional, Any
from utils.logger import get_logger
import threading

logger = get_logger("ProfileStore")

# Thread-safe lock for concurrent updates
_lock = threading.Lock()

# In-memory store: student_id -> profile dict
_profiles: Dict[str, dict] = {}


def _default_profile(student_id: str) -> dict:
    return {
        "student_id": student_id,
        "weak_topics": [],
        "strong_topics": [],
        "average_score": 0.0,
        "study_hours": 2,
        "learning_pace": "Normal learner",
        "consistency": "Medium",
        "preferred_difficulty": "Medium",
        "last_activity": None,
        # Running quiz history (last 50 entries)
        "quiz_history": [],
        # Aggregated topic scores: {topic: [list of scores]}
        "_topic_scores": {},
        # Session memory for Mentor AI (last 10 session summaries)
        "mentor_session_memory": [],
        # Performance prediction cache
        "performance_snapshot": None,
    }


def get_profile(student_id: str) -> dict:
    """Return the profile for a student, creating a default one if missing."""
    with _lock:
        if student_id not in _profiles:
            _profiles[student_id] = _default_profile(student_id)
            logger.info(f"Created new profile for student '{student_id}'")
        return dict(_profiles[student_id])


def upsert_profile(student_id: str, updates: dict) -> dict:
    """
    Merge top-level keys from `updates` into the stored profile.
    Protected keys like _topic_scores are not overwritten via this method.
    """
    with _lock:
        if student_id not in _profiles:
            _profiles[student_id] = _default_profile(student_id)
        profile = _profiles[student_id]
        for key, value in updates.items():
            if not key.startswith("_"):  # Don't allow overwriting internal keys
                profile[key] = value
        logger.info(f"Upserted profile for student '{student_id}'")
        return dict(profile)


def ingest_quiz_record(student_id: str, quiz: dict) -> None:
    """
    Add a quiz record to the student's profile and recompute aggregates:
    - weak_topics / strong_topics
    - average_score
    - learning_pace
    - consistency
    - preferred_difficulty
    """
    with _lock:
        if student_id not in _profiles:
            _profiles[student_id] = _default_profile(student_id)
        profile = _profiles[student_id]

        # Append to rolling history (keep last 50)
        profile["quiz_history"].append(quiz)
        if len(profile["quiz_history"]) > 50:
            profile["quiz_history"] = profile["quiz_history"][-50:]

        # Update per-topic scores
        topic = quiz.get("topic", "Unknown")
        score = quiz.get("score", 0)
        if topic not in profile["_topic_scores"]:
            profile["_topic_scores"][topic] = []
        profile["_topic_scores"][topic].append(score)

        # Recompute weak / strong topics
        weak, strong = [], []
        for t, scores in profile["_topic_scores"].items():
            avg = sum(scores) / len(scores)
            if avg < 60:
                weak.append(t)
            elif avg >= 75:
                strong.append(t)
        profile["weak_topics"] = weak
        profile["strong_topics"] = strong

        # Recompute overall average score
        all_scores = [q.get("score", 0) for q in profile["quiz_history"]]
        profile["average_score"] = round(sum(all_scores) / len(all_scores), 1)

        # Detect learning pace
        total_time = sum(q.get("completion_time_seconds", 30) for q in profile["quiz_history"])
        total_ques = sum(q.get("total_questions", 1) for q in profile["quiz_history"])
        avg_time_per_q = total_time / total_ques if total_ques > 0 else 30
        avg = profile["average_score"]

        if avg >= 80 and avg_time_per_q < 25:
            profile["learning_pace"] = "Fast learner"
        elif avg < 60 or avg_time_per_q > 50:
            profile["learning_pace"] = "Needs revision"
        else:
            profile["learning_pace"] = "Normal learner"

        # Detect consistency (based on variance in scores)
        if len(all_scores) >= 3:
            mean = sum(all_scores) / len(all_scores)
            variance = sum((s - mean) ** 2 for s in all_scores) / len(all_scores)
            std_dev = variance ** 0.5
            if std_dev < 10:
                profile["consistency"] = "High"
            elif std_dev < 20:
                profile["consistency"] = "Medium"
            else:
                profile["consistency"] = "Low"

        # Adapt preferred difficulty based on recent average
        if avg >= 80:
            profile["preferred_difficulty"] = "Hard"
        elif avg < 50:
            profile["preferred_difficulty"] = "Easy"
        else:
            profile["preferred_difficulty"] = "Medium"

        profile["last_activity"] = quiz.get("completed_at", None)
        logger.info(f"Ingested quiz for student '{student_id}': topic={topic}, score={score}")


def add_mentor_session(student_id: str, summary: str) -> None:
    """Append a mentor session summary to the student's memory (keep last 10)."""
    with _lock:
        if student_id not in _profiles:
            _profiles[student_id] = _default_profile(student_id)
        profile = _profiles[student_id]
        profile["mentor_session_memory"].append(summary)
        if len(profile["mentor_session_memory"]) > 10:
            profile["mentor_session_memory"] = profile["mentor_session_memory"][-10:]
        logger.info(f"Stored mentor session memory for student '{student_id}'")


def set_performance_snapshot(student_id: str, snapshot: dict) -> None:
    """Cache the latest performance prediction for a student."""
    with _lock:
        if student_id not in _profiles:
            _profiles[student_id] = _default_profile(student_id)
        _profiles[student_id]["performance_snapshot"] = snapshot
        logger.info(f"Saved performance snapshot for student '{student_id}'")


def list_student_ids() -> List[str]:
    with _lock:
        return list(_profiles.keys())
