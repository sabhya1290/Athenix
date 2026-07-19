"""
Athenix Python Backend AI Service Integration

Helper module to communicate from django/flask backend to FastAPI AI microservice.
"""

import os
import requests
from typing import Dict, List, Any

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8000")

def get_explanation(topic: str) -> Dict[str, Any]:
    """1. EXPLAIN → Explanation Screen"""
    try:
        response = requests.post(f"{AI_SERVICE_URL}/explain", json={"topic": topic}, timeout=20)
        return response.json()
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

def generate_quiz(topic: str, difficulty: str = "Easy", questions: int = 5) -> Dict[str, Any]:
    """2. QUIZ → Quiz Builder"""
    try:
        response = requests.post(
            f"{AI_SERVICE_URL}/generate-quiz",
            json={"topic": topic, "difficulty": difficulty, "questions": questions},
            timeout=20
        )
        return response.json()
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

def generate_roadmap(
    exam: str,
    days_left: int,
    subjects: List[str],
    daily_hours: int,
    weak_topics: List[str] = None,
    strong_topics: List[str] = None
) -> Dict[str, Any]:
    """3. ROADMAP → Planner Screen"""
    if weak_topics is None:
        weak_topics = []
    if strong_topics is None:
        strong_topics = []
    try:
        response = requests.post(
            f"{AI_SERVICE_URL}/roadmap",
            json={
                "exam": exam,
                "days_left": days_left,
                "subjects": subjects,
                "daily_hours": daily_hours,
                "weak_topics": weak_topics,
                "strong_topics": strong_topics
            },
            timeout=20
        )
        return response.json()
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

def get_recommendation(profile: Dict[str, Any]) -> Dict[str, Any]:
    """2.5 RECOMMEND → Recommendation Engine"""
    try:
        response = requests.post(
            f"{AI_SERVICE_URL}/recommend",
            json=profile,
            timeout=20
        )
        return response.json()
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

def evaluate_answer(question: str, student_answer: str) -> Dict[str, Any]:
    """4. EVALUATE → Answer Checker"""
    try:
        response = requests.post(
            f"{AI_SERVICE_URL}/evaluate",
            json={"question": question, "student_answer": student_answer},
            timeout=20
        )
        return response.json()
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

def analyze_performance(quizzes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """5. ANALYZE → Analytics Dashboard"""
    try:
        response = requests.post(f"{AI_SERVICE_URL}/analyze", json={"quizzes": quizzes}, timeout=20)
        return response.json()
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

def get_skill_gaps(quizzes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """5.5 SKILL GAP → Skill Gap Detection"""
    try:
        response = requests.post(f"{AI_SERVICE_URL}/skill-gap", json={"quizzes": quizzes}, timeout=20)
        return response.json()
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

def check_ai_health() -> Dict[str, Any]:
    """AI Service Health Check"""
    try:
        response = requests.get(f"{AI_SERVICE_URL}/health", timeout=5)
        return response.json()
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}
