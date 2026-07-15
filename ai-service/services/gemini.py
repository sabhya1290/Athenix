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

def generate_text(prompt: str, json_mode: bool = False) -> str:
    """
    Sends a prompt to the Gemini model and returns the text response.
    
    If json_mode is True, forces Gemini to respond with valid JSON.
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
        
    response = model.generate_content(prompt, generation_config=generation_config)
    return response.text
