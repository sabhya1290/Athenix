import os
# pyrefly: ignore [missing-import]
import google.generativeai as genai
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

# Configure the API key
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

from utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
import logging

logger = get_logger("GeminiService")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
def generate_text_call(model: genai.GenerativeModel, prompt: str, generation_config: dict) -> str:
    try:
        logger.info("Initiating Gemini API content generation call...")
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            request_options={"timeout": 15.0}  # 15 seconds timeout
        )
        logger.info("Gemini API call succeeded.")
        return response.text
    except Exception as e:
        logger.error(f"Gemini API call failed: {str(e)}")
        raise e

def generate_text(prompt: str, json_mode: bool = False, response_schema=None) -> str:
    """
    Sends a prompt to the Gemini model and returns the text response.
    
    If json_mode is True, forces Gemini to respond with valid JSON.
    If response_schema is provided, forces Gemini to output matching the Pydantic schema.
    Uses retry logic and a 15-second timeout for stability.
    """
    current_key = api_key or os.getenv("GEMINI_API_KEY")
    if not current_key:
        raise ValueError("GEMINI_API_KEY is not set. Please add it to your .env file.")
    
    # Configure on call if it was updated in .env
    genai.configure(api_key=current_key)
    
    model = genai.GenerativeModel("gemini-3.5-flash")
    
    generation_config = {}
    if json_mode:
        generation_config["response_mime_type"] = "application/json"
    if response_schema:
        generation_config["response_schema"] = response_schema
        
    return generate_text_call(model, prompt, generation_config)
