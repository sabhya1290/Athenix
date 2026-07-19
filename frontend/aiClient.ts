/**
 * Athenix Frontend AI Service Client
 * 
 * This client integrates your frontend pages with the FastAPI AI Microservice.
 * Configure the base URL using the environment variable or fallback to localhost.
 */

import axios from 'axios';

const AI_SERVICE_URL = process.env.REACT_APP_AI_SERVICE_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: AI_SERVICE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface UnifiedResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
}

// -------------------------------------------------------------
// 1. EXPLAIN → Explanation Screen
// -------------------------------------------------------------
export interface ExplainResponse {
  answer: string;
}

export async function getExplanation(topic: string): Promise<UnifiedResponse<ExplainResponse>> {
  try {
    const response = await client.post<UnifiedResponse<ExplainResponse>>('/explain', { topic });
    return response.data;
  } catch (error: any) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to fetch explanation',
    };
  }
}

// -------------------------------------------------------------
// 2. QUIZ → Quiz Builder
// -------------------------------------------------------------
export interface QuizItem {
  question: string;
  options: string[];
  answer: string; // A, B, C, or D
  explanation: string;
}

export interface QuizResponse {
  quiz: QuizItem[];
  adapted_difficulty: 'Easy' | 'Medium' | 'Hard';
}

export async function generateQuiz(
  topic: string,
  difficulty: 'Easy' | 'Medium' | 'Hard' = 'Easy',
  questions: number = 5,
  recent_scores?: number[]
): Promise<UnifiedResponse<QuizResponse>> {
  try {
    const response = await client.post<UnifiedResponse<QuizResponse>>('/generate-quiz', {
      topic,
      difficulty,
      questions,
      recent_scores,
    });
    return response.data;
  } catch (error: any) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to generate quiz',
    };
  }
}

// -------------------------------------------------------------
// 3. ROADMAP → Planner Screen
// -------------------------------------------------------------
export interface PlannerResponse {
  plan: Record<string, string[]>; // e.g. {"Day 1": ["Study X", "Revise Y"]}
}

export async function generateRoadmap(
  exam: string,
  daysLeft: number,
  subjects: string[],
  dailyHours: number,
  weakTopics: string[] = [],
  strongTopics: string[] = []
): Promise<UnifiedResponse<PlannerResponse>> {
  try {
    const response = await client.post<UnifiedResponse<PlannerResponse>>('/roadmap', {
      exam,
      days_left: daysLeft,
      subjects,
      daily_hours: dailyHours,
      weak_topics: weakTopics,
      strong_topics: strongTopics,
    });
    return response.data;
  } catch (error: any) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to generate roadmap',
    };
  }
}

// -------------------------------------------------------------
// 3.5 RECOMMEND → Recommendation Engine
// -------------------------------------------------------------
export interface WeakTopicDetail {
  topic: string;
  importance: 'High' | 'Medium' | 'Low';
  exam_weightage: string; // e.g. "12%" or "High"
  past_mistakes_count: number;
}

export interface StudentProfileRequest {
  subjects: string[];
  weak_topics: WeakTopicDetail[];
  strong_topics: string[];
  average_score: number;
  learning_pace: 'Slow' | 'Medium' | 'Fast';
  study_hours: number;
  consistency: 'High' | 'Medium' | 'Low';
  last_studied: string;
  preferred_difficulty: 'Easy' | 'Medium' | 'Hard';
  days_left: number;
}

export interface RecommendationResponse {
  recommendation: string;
}

export async function getRecommendation(
  profile: StudentProfileRequest
): Promise<UnifiedResponse<RecommendationResponse>> {
  try {
    const response = await client.post<UnifiedResponse<RecommendationResponse>>('/recommend', profile);
    return response.data;
  } catch (error: any) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to fetch recommendation',
    };
  }
}

// -------------------------------------------------------------
// 4. EVALUATE → Answer Checker
// -------------------------------------------------------------
export interface EvaluationResponse {
  score: number; // score out of 10
  feedback: string;
  improvement: string;
}

export async function evaluateAnswer(
  question: string,
  studentAnswer: string
): Promise<UnifiedResponse<EvaluationResponse>> {
  try {
    const response = await client.post<UnifiedResponse<EvaluationResponse>>('/evaluate', {
      question,
      student_answer: studentAnswer,
    });
    return response.data;
  } catch (error: any) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to evaluate answer',
    };
  }
}

// -------------------------------------------------------------
// 5. ANALYZE → Analytics Dashboard
// -------------------------------------------------------------
export interface QuizRecord {
  title: string;
  topic: string;
  score: number; // percentage (0-100)
}

export interface AnalyticsResponse {
  weak_topics: string[];
  strong_topics: string[];
  topic_mastery: Record<string, number>;
  weakness_graph: Record<string, number>;
  learning_trend: string;
  improvement_pct: number;
  confidence_score: number;
  accuracy_by_subject: Record<string, number>;
  time_spent: Record<string, number>;
  predicted_rank: string;
  predicted_exam_readiness: number;
  detected_learning_pace: 'Fast learner' | 'Normal learner' | 'Needs revision';
  expected_score: number;
  probability_of_clearing_exam: 'High' | 'Medium' | 'Low';
}

export async function analyzePerformance(
  quizzes: QuizRecord[]
): Promise<UnifiedResponse<AnalyticsResponse>> {
  try {
    const response = await client.post<UnifiedResponse<AnalyticsResponse>>('/analyze', { quizzes });
    return response.data;
  } catch (error: any) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to analyze performance',
    };
  }
}

// -------------------------------------------------------------
// 5.5 SKILL GAP → Skill Gap Detection
// -------------------------------------------------------------
export interface SkillGapItem {
  topic: string;
  reason: string;
  priority: 'High' | 'Medium' | 'Low';
  gaps_resources: string[];
}

export interface SkillGapResponse {
  gaps: SkillGapItem[];
}

export async function getSkillGaps(
  quizzes: QuizRecord[]
): Promise<UnifiedResponse<SkillGapResponse>> {
  try {
    const response = await client.post<UnifiedResponse<SkillGapResponse>>('/skill-gap', { quizzes });
    return response.data;
  } catch (error: any) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to detect skill gaps',
    };
  }
}

// -------------------------------------------------------------
// 6. MENTOR AI → Conversational Chat & Tutoring
// -------------------------------------------------------------
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface MentorChatRequest {
  message: string;
  chat_history?: ChatMessage[];
  weak_topics?: string[];
  doc_id?: string;
}

export interface MentorChatResponse {
  response: string;
  retrieved_context?: string[];
}

export async function mentorChat(
  payload: MentorChatRequest
): Promise<UnifiedResponse<MentorChatResponse>> {
  try {
    const response = await client.post<UnifiedResponse<MentorChatResponse>>('/mentor/chat', payload);
    return response.data;
  } catch (error: any) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Mentor AI chat failed',
    };
  }
}

// -------------------------------------------------------------
// HEALTH CHECK
// -------------------------------------------------------------
export interface HealthResponse {
  status: string;
  service: string;
}

export async function checkAIHealth(): Promise<UnifiedResponse<HealthResponse>> {
  try {
    const response = await client.get<UnifiedResponse<HealthResponse>>('/health');
    return response.data;
  } catch (error: any) {
    return {
      success: false,
      data: null,
      error: error.message || 'AI service is offline',
    };
  }
}
