/**
 * Athenix Node.js/Express Backend AI Service Integration
 * 
 * Helper service to proxy calls from express backend to FastAPI AI microservice.
 */

const axios = require('axios');

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: AI_SERVICE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

/**
 * 1. EXPLAIN → Explanation Screen
 */
async function getExplanation(topic) {
  try {
    const response = await client.post('/explain', { topic });
    return response.data;
  } catch (error) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to fetch explanation'
    };
  }
}

/**
 * 2. QUIZ → Quiz Builder
 */
async function generateQuiz(topic, difficulty = 'Easy', questions = 5) {
  try {
    const response = await client.post('/generate-quiz', { topic, difficulty, questions });
    return response.data;
  } catch (error) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to generate quiz'
    };
  }
}

/**
 * 3. ROADMAP → Planner Screen
 */
async function generateRoadmap(exam, daysLeft, subjects, dailyHours, weakTopics = [], strongTopics = []) {
  try {
    const response = await client.post('/roadmap', {
      exam,
      days_left: daysLeft,
      subjects,
      daily_hours: dailyHours,
      weak_topics: weakTopics,
      strong_topics: strongTopics
    });
    return response.data;
  } catch (error) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to generate roadmap'
    };
  }
}

/**
 * 4. EVALUATE → Answer Checker
 */
async function evaluateAnswer(question, studentAnswer) {
  try {
    const response = await client.post('/evaluate', {
      question,
      student_answer: studentAnswer
    });
    return response.data;
  } catch (error) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to evaluate answer'
    };
  }
}

/**
 * 5. ANALYZE → Analytics Dashboard
 */
async function analyzePerformance(quizzes) {
  try {
    const response = await client.post('/analyze', { quizzes });
    return response.data;
  } catch (error) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to analyze performance'
    };
  }
}

/**
 * 2.5 RECOMMEND → Recommendation Engine
 */
async function getRecommendation(profile) {
  try {
    const response = await client.post('/recommend', profile);
    return response.data;
  } catch (error) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to fetch recommendation'
    };
  }
}

/**
 * 5.5 SKILL GAP → Skill Gap Detection
 */
async function getSkillGaps(quizzes) {
  try {
    const response = await client.post('/skill-gap', { quizzes });
    return response.data;
  } catch (error) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Failed to detect skill gaps'
    };
  }
}

/**
 * 6. MENTOR AI → Conversational Chat & Tutoring
 */
async function mentorChat(payload) {
  try {
    const response = await client.post('/mentor/chat', payload);
    return response.data;
  } catch (error) {
    return {
      success: false,
      data: null,
      error: error.response?.data?.detail || error.message || 'Mentor AI chat failed'
    };
  }
}

/**
 * Health Check
 */
async function checkAIHealth() {
  try {
    const response = await client.get('/health');
    return response.data;
  } catch (error) {
    return {
      success: false,
      data: null,
      error: error.message || 'AI service is offline'
    };
  }
}

module.exports = {
  getExplanation,
  generateQuiz,
  generateRoadmap,
  getRecommendation,
  evaluateAnswer,
  analyzePerformance,
  getSkillGaps,
  mentorChat,
  checkAIHealth
};
