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
