import google.generativeai as genai
import logging
from app.config.config import GEMINI_API_KEY, GENERATION_CONFIG

logger = logging.getLogger(__name__)

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables")
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

def generate_content(prompt, model_name='gemini-2.0-flash'):
    try:
        model = genai.GenerativeModel(model_name, generation_config=GENERATION_CONFIG)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        raise
