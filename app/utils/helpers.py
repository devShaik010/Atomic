import json
import time
import logging
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
    if "```json" in response_text:
        json_str = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        json_str = response_text.split("```")[1].strip()
    else:
        json_str = response_text.strip()
    
    return json.loads(json_str)

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
