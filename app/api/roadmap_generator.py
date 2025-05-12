from flask import Blueprint, request, jsonify
import logging
import time
import traceback
from app.models.gemini_model import generate_content
from app.utils.helpers import parse_ai_json, validate_roadmap, retry_on_exception
from app.config.config import ERROR_MESSAGES

roadmap_bp = Blueprint('roadmap', __name__)
logger = logging.getLogger(__name__)

@roadmap_bp.route('/generate-roadmap', methods=['POST'])
def generate_roadmap():
    start_time = time.time()
    
    try:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": ERROR_MESSAGES['invalid_json']}), 400
        except Exception:
            return jsonify({"error": ERROR_MESSAGES['invalid_json']}), 400
        
        if not data or 'course_title' not in data or 'level' not in data:
            return jsonify({"error": ERROR_MESSAGES['missing_fields']}), 400
            
        course_title = data['course_title'].strip()
        level = data['level'].strip()
        
        logger.info(f"Generating roadmap for course: '{course_title}', level: '{level}'")
        
        prompt = f"""
        Generate a structured course roadmap for a {level} level course titled "{course_title}".
        
        The response should be in valid JSON format with the following structure:
        {{"course_title": "Frontend Developer",
        "description": "Learn how to build modern, responsive websites using HTML, CSS, and JavaScript.",
        "level": "Beginner",
        "duration": "3 months",
        "modules": [
            {{"module_title": "Introduction to Web", "topics": ["How the Web Works", "Browsers and Servers", "HTTP Basics"]}},
            {{"module_title": "HTML Basics", "topics": ["HTML Tags", "Forms", "Semantic HTML"]}}]}}
        
        Make sure to include:
        1. A descriptive title matching the input course_title
        2. A concise but informative description
        3. The correct level as provided in the input
        4. A realistic duration (e.g., "3 months", "6 weeks")
        5. At least 4-6 modules with relevant topics for each module
        
        The modules should follow a logical progression and cover all essential topics for a {level} level {course_title} course.
        
        IMPORTANT: The response must be valid JSON without any markdown formatting, code blocks, or extra text.
        """
        
        try:
            response_text = generate_content(prompt)
        except Exception:
            return jsonify({
                "error": ERROR_MESSAGES['ai_generation_failed'],
                "message": "Our AI service is currently experiencing issues. Please try again in a few minutes."
            }), 503
        
        try:
            roadmap = parse_ai_json(response_text)
        except Exception as e:
            logger.error(f"JSON parsing error: {str(e)}\nResponse: {response_text}")
            return jsonify({
                "error": ERROR_MESSAGES['json_parse_error'],
                "message": "We encountered an issue processing the AI response. Please try again."
            }), 500
        
        is_valid, validation_error = validate_roadmap(roadmap)
        if not is_valid:
            logger.warning(f"Invalid roadmap structure: {validation_error}\nRoadmap: {roadmap}")
            return jsonify({
                "error": "Generated roadmap is incomplete",
                "message": "Please try again. If the issue persists, try with different input parameters."
            }), 500
        
        processing_time = time.time() - start_time
        logger.info(f"Successfully generated roadmap in {processing_time:.2f}s")
        
        return jsonify(roadmap), 200
            
    except Exception as e:
        logger.error(f"Unexpected error in generate_roadmap: {str(e)}\n{traceback.format_exc()}")
        
        return jsonify({
            "error": ERROR_MESSAGES['server_error'],
            "message": "An unexpected error occurred. Please try again later."
        }), 500
