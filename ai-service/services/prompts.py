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
    formatted_quizzes = "\n".join([
        f"- {q.get('title', 'Quiz')}: {q.get('topic')} | Score: {q.get('score')}% | "
        f"Time: {q.get('completion_time_seconds')}s | Correct: {q.get('correct_answers')}/{q.get('total_questions')} | "
        f"Difficulty: {q.get('difficulty')}"
        for q in quizzes
    ])
    return f"""You are a deep-learning diagnostic system. Perform a comprehensive analysis of the student's quiz history:
{formatted_quizzes}

Formulate and calculate the following metrics:
1. **Weak topics**: List of topics where the student consistently scored low (e.g. < 60%).
2. **Strong topics**: List of topics where the student consistently scored high (e.g. >= 80%).
3. **Topic mastery**: A dictionary mapping each unique topic name to a percentage mastery value (0 to 100).
4. **Weakness graph**: A dictionary mapping each weak topic to a calculated weakness priority or error rate (0.0 to 1.0).
5. **Learning trend**: "Improving" if recent scores are higher, "Declining" if lower, or "Stable".
6. **Improvement %**: Percentage growth or improvement rate compared to earlier quiz attempts.
7. **Confidence score**: An estimated confidence score (0 to 100) based on average performance and consistency.
8. **Accuracy by subject**: Accuracy percentage (0 to 100) grouped by major subject category.
9. **Time spent**: Estimated study time spent in minutes per subject category (invent a realistic allocation based on scores).
10. **Predicted rank**: An estimated competition rank range (e.g., "Top 1000", "Top 5%", "Rank 2000-2500") based on performance.
11. **Predicted exam readiness**: Exam readiness percentage (0 to 100) based on topic mastery.
12. **Detected learning pace**: Categorize the student as either "Fast learner" (high scores, low completion times on harder quizzes), "Normal learner" (average score and time), or "Needs revision" (low accuracy or extremely slow completion times).

Return the response in valid JSON format matching this schema:
{{
  "weak_topics": ["List of weak topics"],
  "strong_topics": ["List of strong topics"],
  "topic_mastery": {{"Topic A": 85.0, "Topic B": 40.0}},
  "weakness_graph": {{"Topic B": 0.8, "Topic C": 0.5}},
  "learning_trend": "Improving",
  "improvement_pct": 12.5,
  "confidence_score": 75.0,
  "accuracy_by_subject": {{"Math": 85.0, "Physics": 50.0}},
  "time_spent": {{"Math": 240, "Physics": 480}},
  "predicted_rank": "Top 10%",
  "predicted_exam_readiness": 78.0,
  "detected_learning_pace": "Fast learner"
}}

Do not wrap the response in markdown code blocks like ```json ... ```. Return raw JSON only."""

def get_skill_gap_prompt(quizzes: list) -> str:
    formatted_quizzes = "\n".join([
        f"- {q.get('title', 'Quiz')}: {q.get('topic')} | Score: {q.get('score')}% | "
        f"Time: {q.get('completion_time_seconds')}s | Correct: {q.get('correct_answers')}/{q.get('total_questions')} | "
        f"Difficulty: {q.get('difficulty')}"
        for q in quizzes
    ])
    return f"""You are an educational diagnostician. Analyze the student's historical quiz records:
{formatted_quizzes}

Detect the student's skill gaps (topics where the student is failing, making frequent mistakes, or struggling with time).
For each detected skill gap, determine:
1. **Topic**: The specific topic/concept.
2. **Reason**: A detailed reason describing what the student is struggling with (e.g. "Struggling with definite integrals, spending over 60 seconds per question on simple integration, showing basic conceptual gaps").
3. **Priority**: "High" (score < 50% or very slow), "Medium" (score 50-70%), or "Low" (score 70-80% but needs small improvement).
4. **Resources**: A list of recommended textbooks, chapters, tutorials, or video topics to help close the gap.

Return the response in valid JSON format matching this schema:
{{
  "gaps": [
    {{
      "topic": "Calculus",
      "reason": "Struggles with integral calculus formulas and speed",
      "priority": "High",
      "gaps_resources": ["NCERT Mathematics Class 12 Chapter 7", "Khan Academy definite integrals playlist"]
    }}
  ]
}}

Note: the key for the resource list must be precisely "gaps_resources".
Do not wrap the response in markdown code blocks like ```json ... ```. Return raw JSON only."""

