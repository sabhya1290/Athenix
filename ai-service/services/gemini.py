import os
# pyrefly: ignore [missing-import]
import google.generativeai as genai
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

# Configure the API key
api_key = os.getenv("GEMINI_API_KEY")

from utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json

logger = get_logger("GeminiService")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
def generate_text_lc(prompt: str, current_key: str, response_schema=None) -> str:
    try:
        logger.info("Initiating LangChain ChatGoogleGenerativeAI chain call...")
        
        # Initialize Google GenAI chat model under LangChain
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            google_api_key=current_key,
            temperature=0.7,
            timeout=15.0  # 15 seconds timeout
        )
        
        # Construct the LangChain Expression Language (LCEL) chain
        prompt_template = PromptTemplate.from_template("{prompt_text}")
        
        if response_schema:
            logger.info("Running structured output schema chain...")
            structured_llm = llm.with_structured_output(response_schema)
            chain = prompt_template | structured_llm
            result = chain.invoke({"prompt_text": prompt})
            
            # Serialize the structured Pydantic object back into JSON text
            if hasattr(result, "model_dump_json"):
                return result.model_dump_json()
            elif hasattr(result, "json"):
                return result.json()
            else:
                return json.dumps(result)
        else:
            logger.info("Running standard string parser chain...")
            chain = prompt_template | llm | StrOutputParser()
            return chain.invoke({"prompt_text": prompt})
            
    except Exception as e:
        logger.error(f"LangChain chain call failed: {str(e)}")
        raise e

def generate_text(prompt: str, json_mode: bool = False, response_schema=None) -> str:
    """
    Sends a prompt to the Gemini model via LangChain and returns the text response.
    
    If response_schema is provided, forces LangChain to output matching the Pydantic schema.
    Uses retry logic and a 15-second timeout for stability.
    """
    current_key = api_key or os.getenv("GEMINI_API_KEY")
    if not current_key:
        raise ValueError("GEMINI_API_KEY is not set. Please add it to your .env file.")
    
    return generate_text_lc(prompt, current_key, response_schema)
