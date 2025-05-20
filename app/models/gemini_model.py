import google.generativeai as genai
import logging
from app.config.config import GEMINI_API_KEY, GENERATION_CONFIG

logger = logging.getLogger(__name__)

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables")
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

def generate_content(prompt, model_name='gemini-2.0-flash', format_type='json'):
    try:
        model = genai.GenerativeModel(model_name, generation_config=GENERATION_CONFIG)
        
        if format_type == 'markdown':
            prompt_with_instructions = f"{prompt}\n\nIMPORTANT: Return your response as structured markdown with headings, bullet points, and code blocks where appropriate. DO NOT return JSON."
        else:
            prompt_with_instructions = f"{prompt}\n\nIMPORTANT: Return ONLY valid JSON without any additional text, markdown formatting, or code blocks."
        
        response = model.generate_content(prompt_with_instructions)
        response_text = response.text.strip()
        
        if format_type == 'json' and not response_text.startswith('{'):
            if '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                response_text = response_text[start:end]
            else:
                raise ValueError("Response does not contain valid JSON")
        
        return response_text
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        raise
