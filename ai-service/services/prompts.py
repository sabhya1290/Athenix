def get_explain_prompt(topic: str) -> str:
    return f"""You are an expert teacher.
Explain "{topic}".
Use simple English.
Give one analogy.
Give one example.
Keep it under 300 words."""

def get_quiz_prompt(topic: str, difficulty: str, questions: int) -> str:
    return f"""Generate a quiz with {questions} {difficulty} Multiple Choice Questions (MCQs) on the topic: "{topic}".
Each question must have exactly 4 options, a correct answer, and a short explanation.

You must return the response in valid JSON matching this schema:
{{
  "quiz": [
    {{
      "question": "question text here",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "A/B/C/D",
      "explanation": "explanation text here"
    }}
  ]
}}

Do not wrap the output in markdown code blocks like ```json ... ```. Return raw JSON only."""

def get_recommendation_prompt(profile: dict) -> str:
    subjects = ", ".join(profile.get("subjects", []))
    strong = ", ".join(profile.get("strong_topics", []))
    
    # Format weak topics list with detailed parameters
    weak_details_list = []
    for wt in profile.get("weak_topics", []):
        detail = (
            f"- Topic: '{wt.get('topic')}' "
            f"(Importance: {wt.get('importance')}, "
            f"Exam Weightage: {wt.get('exam_weightage')}, "
            f"Past Mistakes: {wt.get('past_mistakes_count')} times)"
        )
        weak_details_list.append(detail)
    weak_formatted = "\n".join(weak_details_list)
    
    return f"""You are an expert adaptive academic advisor. Provide a highly customized study recommendation and daily learning plan for a student based on their learning profile:

- **Subjects studying**: {subjects}
- **Weak topics breakdown**:
{weak_formatted}
- **Strong topics/concepts**: {strong}
- **Average score across quizzes**: {profile.get("average_score")}%
- **Learning pace**: {profile.get("learning_pace")}
- **Daily study hours allocated**: {profile.get("study_hours")} hours
- **Study consistency**: {profile.get("consistency")}
- **Days left until the exam**: {profile.get("days_left")} days
- **Preferred difficulty level**: {profile.get("preferred_difficulty")}

Formulate an ADAPTIVE study plan today by applying these rules:
1. Prioritize weak topics based on their Importance, Exam Weightage, and the count of Past Mistakes (tackle high-impact, error-prone topics first).
2. Adapt the study plan depth based on "Days left until the exam". If the exam is close (< 7 days), recommend highly focused high-yield revision and past-paper drills. If the exam is far (> 30 days), recommend deep conceptual reading and problem-solving.
3. Adapt the intensity and structure to match their "Learning pace" and "Study consistency".

Return the response in valid JSON format matching this schema:
{{
  "recommendation": "your highly customized, adaptive study plan and recommendation text here"
}}

Do not wrap the response in markdown code blocks like ```json ... ```. Return raw JSON only."""

def get_roadmap_prompt(exam: str, days_left: int, subjects: list, daily_hours: int, weak_topics: list, strong_topics: list) -> str:
    formatted_subjects = ", ".join(subjects)
    formatted_weak = ", ".join(weak_topics)
    formatted_strong = ", ".join(strong_topics)
    return f"""Create a highly personalized day-wise study roadmap for the {exam} exam.
Subjects: {formatted_subjects}
Time Left: {days_left} days
Weak Topics: {formatted_weak}
Strong Topics: {formatted_strong}
Daily study allocation: {daily_hours} hours.

Ensure the plan follows these instructions:
- Place heavier daily focus and initial blocks on strengthening the specified Weak Topics.
- Keep Strong Topics in a lighter maintenance review loop (revision & quick mock tests).
- Distribute the study hours across the days logically.
- Maintain a structured day-by-day task checklist format for the student.

Return the response in valid JSON format matching this schema:
{{
  "plan": {{
    "Day 1": ["Study block 1: Calculus integration (3 hours)", "Study block 2: chemistry formula cards (2 hours)"],
    "Day 2": ["Study block 1: Calculus differentiation (3 hours)", "Study block 2: physics notes (2 hours)"]
  }}
}}

Do not wrap the response in markdown code blocks like ```json ... ```. Return raw JSON only."""

def get_evaluation_prompt(question: str, student_answer: str) -> str:
    return f"""You are an expert evaluator. Evaluate the student's answer for the given question.
Question: "{question}"
Student's Answer: "{student_answer}"

Provide:
- A score out of 10
- Feedback pointing out mistakes, positive aspects of the answer, and what constitutes the correct/complete answer
- Specific improvements needed (e.g., "Mention sorted array.")

Return the response in valid JSON format matching this schema:
{{
  "score": 8,
  "feedback": "your feedback text here",
  "improvement": "your improvement suggestions here"
}}

Do not wrap the response in markdown code blocks like ```json ... ```. Return raw JSON only."""

def get_analytics_prompt(quizzes: list) -> str:
    formatted_quizzes = "\n".join([f"- {q.get('title', 'Quiz')}: {q.get('topic')} - {q.get('score')}%" for q in quizzes])
    return f"""Analyze the student's quiz history and performance:
{formatted_quizzes}

Find and output:
- Weak topics (where the student scored low or struggled)
- Strong topics (where the student scored high or did well)

Return the response in valid JSON format matching this schema:
{{
  "weak_topics": ["List of weak topics"],
  "strong_topics": ["List of strong topics"]
}}

Do not wrap the response in markdown code blocks like ```json ... ```. Return raw JSON only."""
