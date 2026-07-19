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
  "weakness_priorities": [
    {{
      "topic": "Calculus",
      "calculated_priority_score": 85,
      "priority_level": "High",
      "actionable_plan": "Spend 2.5 hours studying definite integrals, focus on limits and NCERT chapter 7."
    }}
  ],
  "daily_allocated_hours": {{
    "Calculus": 2.5,
    "Chemistry": 1.5
  }},
  "exam_readiness_outlook": "The student has strong chemistry fundamentals but critical gaps in calculus which must be resolved to clear the target exam. Days left: {profile.get('days_left')}.",
  "recommendation": "Calculus integration is the highest priority. We have allocated 2.5 daily hours to it."
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
13. **Expected score**: Predict an expected score on a scale of 0 to 300 (e.g. 160).
14. **Probability of clearing exam**: Predict the likelihood of clearing the target exam (High, Medium, or Low).

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
  "detected_learning_pace": "Fast learner",
  "expected_score": 160,
  "probability_of_clearing_exam": "High"
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

Analyze the student's performance to build a structured diagnostic profile:
1. **Topic Accuracy**: Calculate the percentage accuracy (0 to 100) for each unique topic.
2. **Gap Analysis**: For any topic with < 70% accuracy (or where speed is very slow), perform a deep gap analysis explaining what conceptual errors they are making.
3. **Priority Ranking**: Rank each gap as "High" (score < 50%), "Medium" (score 50-70%), or "Low".
4. **Recommended Action**: Define a highly specific, concrete study or practice action (e.g. "Practice 15 integration by parts exercises and review NCERT Chapter 7.2").

Return the response in valid JSON format matching this schema:
{{
  "topic_accuracies": {{
    "Calculus": 40.0,
    "Organic Chemistry": 90.0
  }},
  "gaps": [
    {{
      "topic": "Calculus",
      "gap_analysis": "Struggles with integral calculus formulas, spends over 60 seconds per question, and lacks conceptual clarity on limits.",
      "priority_ranking": "High",
      "recommended_action": "Review limits, practice 15 integration by parts exercises, and complete NCERT Chapter 7.2 drills."
    }}
  ]
}}

Do not wrap the response in markdown code blocks like ```json ... ```. Return raw JSON only."""

def get_mentor_chat_prompt(message: str, history: list, weak_topics: list, context: str, session_memory: list = None) -> str:
    formatted_history = ""
    for msg in history:
        role = "Student" if msg.get("role") == "user" else "Mentor AI"
        formatted_history += f"{role}: {msg.get('content')}\n"

    weak_str = ", ".join(weak_topics) if weak_topics else "None specified"

    # Format persistent memory from previous mentor sessions
    memory_str = ""
    if session_memory:
        memory_str = "\n".join(f"- {m}" for m in session_memory[-5:])  # Use last 5 sessions
    else:
        memory_str = "No previous mentor sessions recorded."

    return f"""You are Mentor AI, an encouraging, patient, and highly intelligent educational guide and tutor. Your goal is to help the student learn effectively, explaining concepts simply and checking in on their understanding.

Here is the complete context available to you:
- **Student's Known Weak Topics**: {weak_str} (Be extra patient and use step-by-step visual analogies for these topics).
- **Student's Past Session Memory** (things discussed in previous sessions):
{memory_str}
- **Retrieved Study Notes / Material Context (RAG)**:
{context or "No specific document context provided."}

If the student asks about something you helped them with before (based on Session Memory), acknowledge it naturally — e.g. "As we discussed last time...". This makes you feel like a real mentor who remembers their student.

Here is the current conversation history:
{formatted_history}

Student's Latest Question:
"{message}"

Provide your tutoring response. Speak directly to the student in a conversational, supportive tone. Keep explanations clear, and if you refer to the notes or past sessions, do so naturally. Do not output JSON, return a standard text response."""

def get_performance_prediction_prompt(quizzes: list, exam: str, days_left: int, profile_context: dict = None) -> str:
    formatted_quizzes = "\n".join([
        f"- {q.get('title', 'Quiz')}: {q.get('topic')} | Score: {q.get('score')}% | "
        f"Time: {q.get('completion_time_seconds')}s | Correct: {q.get('correct_answers')}/{q.get('total_questions')} | "
        f"Difficulty: {q.get('difficulty')}"
        for q in quizzes
    ])

    profile_str = ""
    if profile_context:
        profile_str = f"""
- Learning Pace: {profile_context.get('learning_pace', 'Unknown')}
- Study Consistency: {profile_context.get('consistency', 'Unknown')}
- Daily Study Hours: {profile_context.get('study_hours', 2)}
- Mentor Sessions Completed: {profile_context.get('mentor_sessions', 0)}"""

    return f"""You are an advanced exam performance predictor AI. Based on the student's historical quiz data and learning profile, produce a detailed performance prediction report for the {exam} exam.

Student Quiz History:
{formatted_quizzes}

Days Remaining Until Exam: {days_left} days
Target Exam: {exam}{profile_str}

Using this data, calculate and predict:
1. **Current Readiness %**: A single percentage (0-100) reflecting how ready the student is for the exam RIGHT NOW.
2. **Expected Score**: Predict the score the student would get if they appeared for the {exam} today (scale of 0 to 300).
3. **Probability of Clearing**: Categorize as High (>75% readiness), Medium (50-75%), or Low (<50%).
4. **Critical Weak Topic**: The single most important topic to focus on given the exam date and the student's weaknesses.
5. **Readiness Breakdown**: Subject-level readiness percentages (0-100 for each topic in the quiz data).
6. **Improvement Actions**: Top 3 very specific, actionable steps the student should take in the next 7 days.
7. **Predicted Rank**: Estimated competitive rank range (e.g. "Top 1%", "Top 5000-7000", "Top 20%").
8. **Confidence Message**: A short (1-2 sentence), honest, and encouraging message to the student.

Return the response in valid JSON matching this schema:
{{
  "current_readiness_pct": 72.5,
  "expected_score": 160,
  "probability_of_clearing": "Medium",
  "critical_weak_topic": "Integral Calculus",
  "readiness_breakdown": {{"Calculus": 45.0, "Chemistry": 88.0, "Physics": 70.0}},
  "improvement_actions": [
    "Spend 2 hours daily on Integral Calculus exercises for the next 7 days.",
    "Attempt 1 full-length mock test under timed conditions this weekend.",
    "Review all Calculus mistakes from previous quizzes and make a formula sheet."
  ],
  "predicted_rank": "Top 15%",
  "confidence_message": "You are on the right track! Focus intensively on Calculus this week and your score can jump by 20+ points."
}}

Do not wrap the response in markdown code blocks like ```json ... ```. Return raw JSON only."""

