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
    """
    Parse JSON from AI response with improved error handling and extraction
    This function is designed to handle various edge cases in AI responses
    """
    if not response_text:
        logger.error("Empty response received from AI model")
        raise ValueError("Empty response received from AI model")
        
    # Log the first 200 characters for debugging
    logger.debug(f"Response text (excerpt): {response_text[:200]}...")
    
    try:
        # First, try direct JSON parsing
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If direct parsing fails, try extraction and cleaning
        pass
    
    # Try to extract JSON content from the response
    json_pattern = r'```json\s*(.*?)\s*```|```\s*(.*?)\s*```|\{\s*"[^"]+"\s*:'
    json_matches = re.findall(json_pattern, response_text, re.DOTALL)

    extracted_text = None
    if json_matches:
        # Use the first match that contains valid JSON
        for match_groups in json_matches:
            for group in match_groups:
                if group and group.strip():
                    try:
                        # Check if this looks like the start of a JSON object
                        if group.strip().startswith('{'):
                            extracted_text = group
                            json.loads(extracted_text)
                            break  # Found valid JSON
                    except json.JSONDecodeError:
                        continue  # Try next match
            if extracted_text:
                break
    
    if not extracted_text:
        # No code blocks found, try to find JSON by looking for curly braces
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                extracted_text = response_text[json_start:json_end]
        except Exception as e:
            logger.error(f"Error extracting JSON by braces: {str(e)}")
    
    if not extracted_text:
        # If we still can't find JSON, use the original response
        extracted_text = response_text

    # Clean and fix common issues in the JSON text
    try:
        # Clean the text in case there are unicode or special characters
        cleaned_text = extracted_text.strip()
        
        # Fix common code example issues - this is the critical part
        # Look for code_example fields and ensure they're properly escaped
        code_example_pattern = r'"code_example":\s*"(.*?)(?<!\\)"(?=,|\s*})'
        
        def fix_code_example(match):
            code = match.group(1)
            # Properly escape newlines, quotes and backslashes
            escaped_code = (code
                           .replace('\\', '\\\\')  # Escape backslashes first
                           .replace('\n', '\\n')   # Escape newlines
                           .replace('\r', '\\r')   # Escape carriage returns
                           .replace('"', '\\"'))   # Escape quotes
            return f'"code_example": "{escaped_code}"'
        
        cleaned_text = re.sub(code_example_pattern, fix_code_example, cleaned_text, flags=re.DOTALL)
        
        # Additional cleaning to fix other common JSON issues
        # Fix trailing commas in arrays/objects
        cleaned_text = re.sub(r',\s*}', r'}', cleaned_text)
        cleaned_text = re.sub(r',\s*]', r']', cleaned_text)
        
        # Try to parse the cleaned JSON
        result = json.loads(cleaned_text)
        return result
    except json.JSONDecodeError as e:
        # Log detailed error information for debugging
        logger.error(f"JSON parsing error: {str(e)}")
        logger.error(f"Response excerpt: {extracted_text[:500]}...")
        logger.error(f"JSON error at position {e.pos}: {extracted_text[max(0, e.pos-20):e.pos+20]}")
        
        # As a last resort, try to sanitize the JSON with a regex-based approach
        try:
            # Find all code example fields and completely sanitize them
            pattern = r'("code_example"\s*:\s*)".*?"'
            cleaned_json = re.sub(pattern, r'\1"<code removed for stability>"', extracted_text)
            
            # Try parsing again with sanitized code examples
            result = json.loads(cleaned_json)
            logger.info("Successfully parsed JSON after removing problematic code examples")
            
            return result
        except Exception as sanitize_error:
            logger.error(f"JSON sanitization failed: {str(sanitize_error)}")
            
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
    # Check all required fields
    required_fields = {
        'title': str,
        'level': str,
        'estimated_time': str,
        'overview': str,
        'prerequisites': list,
        'sections': list,
        'practice_exercises': list,
        'additional_resources': list
    }
    
    for field, expected_type in required_fields.items():
        if field not in content:
            return False, f"Missing required field: {field}"
        if not isinstance(content[field], expected_type):
            return False, f"Field '{field}' must be of type {expected_type.__name__}"
    
    # Validate minimum array lengths
    if len(content['prerequisites']) < 1:
        return False, "Must have at least 1 prerequisite"
    
    if len(content['sections']) < 2:
        return False, "Must have at least 2 sections"
    
    if len(content['practice_exercises']) < 1:
        return False, "Must have at least 1 practice exercise"
    
    if len(content['additional_resources']) < 1:
        return False, "Must have at least 1 additional resource"
    
    # Validate section structure
    for section in content['sections']:
        if not isinstance(section, dict):
            return False, "Each section must be an object"
        
        for field in ['section_title', 'content']:
            if field not in section:
                return False, f"Section missing required field: {field}"
            if not isinstance(section[field], str):
                return False, f"Section field '{field}' must be a string"
        
        # Make code_example optional
        if 'code_example' in section and not isinstance(section['code_example'], str):
            return False, "Section field 'code_example' must be a string"
    
    # Validate additional resources structure
    for resource in content['additional_resources']:
        if not isinstance(resource, dict):
            return False, "Each resource must be an object"
        
        for field in ['title', 'url']:
            if field not in resource:
                return False, f"Resource missing required field: {field}"
            if not isinstance(resource[field], str):
                return False, f"Resource field '{field}' must be a string"
    
    return True, ""
