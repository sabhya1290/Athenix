from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from services.gemini import generate_text
from services.prompts import get_mentor_chat_prompt
from services.rag import retrieve_relevant_chunks
from utils.response import UnifiedResponse
from utils.logger import get_logger

logger = get_logger("MentorRoute")
router = APIRouter(prefix="/mentor", tags=["Mentor AI"])

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(..., description="Role of the speaker (user or assistant)")
    content: str = Field(..., description="Content of the message")

class MentorChatRequest(BaseModel):
    message: str = Field(..., example="I don't understand Organic Chemistry.", description="The latest message from the student")
    chat_history: List[ChatMessage] = Field(default=[], description="Previous conversation logs")
    weak_topics: List[str] = Field(default=[], example=["Calculus"], description="The student's weak subjects/topics")
    doc_id: Optional[str] = Field(None, example="3e0d238f-baaf-4cc9-94bb-89c6c79851fe", description="Optional FAISS document ID to query context from")

class MentorChatResponse(BaseModel):
    response: str = Field(..., description="Mentor AI's conversational response")
    retrieved_context: List[str] = Field(default=[], description="The context chunks retrieved from FAISS RAG, if any")

@router.post("/chat", response_model=UnifiedResponse[MentorChatResponse])
def mentor_chat(request: MentorChatRequest):
    logger.info(f"Incoming POST /mentor/chat query: '{request.message[:40]}...'")
    try:
        retrieved_context = []
        context_str = ""
        
        # 1. Retrieve document context from FAISS if doc_id is provided
        if request.doc_id:
            try:
                retrieved_context = retrieve_relevant_chunks(request.doc_id, request.message, k=3)
                context_str = "\n\n---\n\n".join(retrieved_context)
            except Exception as re:
                logger.warning(f"RAG context retrieval failed for doc {request.doc_id}: {str(re)}")
                
        # 2. Build prompt containing message, history, weak topics, and RAG context
        history_list = [h.model_dump() for h in request.chat_history]
        prompt = get_mentor_chat_prompt(request.message, history_list, request.weak_topics, context_str)
        
        # 3. Generate tutoring response
        response_text = generate_text(prompt, json_mode=False)
        
        data = MentorChatResponse(
            response=response_text.strip(),
            retrieved_context=retrieved_context
        )
        logger.info("Successfully generated Mentor AI response.")
        return UnifiedResponse(success=True, data=data)
        
    except Exception as e:
        logger.error(f"Error in Mentor AI chat: {str(e)}")
        # Dynamic fallback response
        weak_str = ", ".join(request.weak_topics)
        fallback_msg = (
            f"Hi there! I am Mentor AI, your virtual tutor. It looks like our AI system is currently offline, "
            f"but I want you to know that you are doing great! I see you have '{weak_str}' listed as areas to focus on. "
            f"Don't worry, organic chemistry and calculus can be tough, but if you break them down and practice daily, you will get it! "
            f"How can I help guide your study session today?"
        )
        data = MentorChatResponse(
            response=fallback_msg,
            retrieved_context=[]
        )
        return UnifiedResponse(success=True, data=data)
