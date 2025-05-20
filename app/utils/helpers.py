import json
import re
import logging
import time
import traceback
from functools import wraps
from app.config.config import MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)

def retry_on_exception(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    logger.warning(f"Retry {retries}/{max_retries} due to: {str(e)}")
                    if retries >= max_retries:
                        logger.error(f"Max retries reached: {str(e)}")
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

def parse_ai_json(response_text):
    """Parse the AI generated response as JSON, with improved handling for math content."""
    if not response_text:
        raise ValueError("Empty response from AI")
    
    try:
        # Try direct JSON parsing first
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        # Log the position of the error
        error_position = e.pos
        error_context = response_text[max(0, error_position-50):min(len(response_text), error_position+50)]
        logger.error(f"JSON error at position {error_position}: {error_context}")
        
        # Special handling for math content - replace common math symbols that break JSON
        sanitized_text = response_text
        math_replacements = {
            "\\": "\\\\",  # Escape backslashes
            "\n": " ",     # Replace newlines with spaces
            "≈": "approximately",
            "∫": "integral",
            "∑": "sum",
            "∞": "infinity",
            "≠": "!=",
            "≤": "<=",
            "≥": ">=",
            "π": "pi",
            "θ": "theta",
            "λ": "lambda",
            "α": "alpha",
            "β": "beta",
            "γ": "gamma",
            "Δ": "Delta",
            "δ": "delta",
            "√": "sqrt"
        }
        
        for symbol, replacement in math_replacements.items():
            sanitized_text = sanitized_text.replace(symbol, replacement)
        
        try:
            return json.loads(sanitized_text)
        except json.JSONDecodeError:
            # If still failing, try more aggressive approach to extract JSON
            try:
                # Find what looks like the start and end of JSON
                json_start = sanitized_text.find('{')
                json_end = sanitized_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    extracted_json = sanitized_text[json_start:json_end]
                    return json.loads(extracted_json)
            except:
                pass
            
            logger.error(f"JSON sanitization failed: {str(e)}")
            raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")

def validate_roadmap(roadmap):
    required_fields = ['course_title', 'description', 'level', 'duration', 'modules']
    for field in required_fields:
        if field not in roadmap:
            return False, f"Missing required field: {field}"
    
    if not isinstance(roadmap['modules'], list) or len(roadmap['modules']) == 0:
        return False, "Modules must be a non-empty list"
    
    for module in roadmap['modules']:
        if 'module_title' not in module or 'topics' not in module:
            return False, "Each module must have a title and topics"
        if not isinstance(module['topics'], list):
            return False, "Topics must be a list"
    
    return True, ""

def validate_tutorial_content(content):
    """Validates the tutorial content structure with relaxed requirements."""
    if not content or not isinstance(content, dict):
        return False, "Invalid or empty content"
    
    required_fields = ['title', 'estimated_time', 'overview', 'sections', 
                      'practice_exercises', 'additional_resources']
    
    # 'about' and 'level' are optional - we'll add them if missing
    for field in required_fields:
        if field not in content:
            return False, f"Missing required field: {field}"
    
    # Validate sections structure
    if not isinstance(content['sections'], list) or not content['sections']:
        return False, "Sections must be a non-empty list"
    
    for section in content['sections']:
        if not isinstance(section, dict) or 'section_title' not in section or 'content' not in section:
            return False, "Each section must contain section_title and content"
    
    return True, "Valid content"
