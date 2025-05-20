from flask import Blueprint, request, jsonify
import logging
import time
import traceback
from app.models.gemini_model import generate_content
from app.utils.helpers import parse_ai_json, retry_on_exception
from app.config.config import ERROR_MESSAGES

quiz_bp = Blueprint('quiz', __name__)
logger = logging.getLogger(__name__)

@quiz_bp.route('/generate-quiz', methods=['POST'])
def generate_quiz():
    start_time = time.time()
    
    try:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": ERROR_MESSAGES['invalid_json']}), 400
        except Exception:
            return jsonify({"error": ERROR_MESSAGES['invalid_json']}), 400
        
        # Extract topic from request
        if 'topic' in data:
            topic = data['topic'].strip()
        else:
            return jsonify({"error": ERROR_MESSAGES['missing_fields']}), 400
        
        # Extract question count or set default
        question_count = int(data.get('count', 5))
        if question_count < 1:
            question_count = 5
        elif question_count > 20:
            question_count = 20  # Limit maximum questions
        
        # Determine difficulty level from user profile or default
        if 'level' in data:
            level = data['level'].strip()
        elif 'user_profile' in data and isinstance(data['user_profile'], dict):
            user_profile = data['user_profile']
            if 'education_level' in user_profile:
                education = user_profile['education_level'].lower()
                if 'phd' in education or 'doctorate' in education:
                    level = "Advanced"
                elif 'master' in education or 'be' in education or 'btech' in education:
                    level = "Intermediate"
                else:
                    level = "Beginner"
            else:
                level = "Intermediate"
        else:
            level = "Intermediate"
            
        logger.info(f"Generating quiz on '{topic}', level: '{level}', questions: {question_count}")
        
        prompt = f"""
        Generate a quiz about "{topic}" for a {level} level learner with {question_count} multiple-choice questions.

        The response should be in valid JSON format with the following structure:
        {{
          "title": "Quiz on JavaScript Promises",
          "description": "Test your knowledge of JavaScript Promises with these multiple-choice questions.",
          "level": "{level}",
          "questions": [
            {{
              "question": "What does a JavaScript Promise represent?",
              "options": [
                "A guaranteed return value",
                "The eventual completion or failure of an asynchronous operation",
                "A special JavaScript function",
                "A type of callback function"
              ],
              "correct_answer": "The eventual completion or failure of an asynchronous operation",
              "explanation": "A Promise in JavaScript represents the eventual completion (or failure) of an asynchronous operation and its resulting value."
            }}
          ]
        }}

        Make sure to:
        1. Create a descriptive title for the quiz
        2. Include a brief description of what the quiz covers
        3. Generate exactly {question_count} multiple-choice questions about {topic}
        4. Each question should have exactly 4 options
        5. Include the correct answer (which must be one of the options)
        6. Provide a brief explanation for why the answer is correct

        CRITICAL FORMATTING INSTRUCTIONS:
        - Ensure all JSON is properly formatted and valid
        - For mathematical content, use plain text to describe formulas
        - Avoid using special characters or symbols
        - Return ONLY the JSON object with no explanations outside the JSON
        """
        
        # Use retry mechanism for AI generation
        @retry_on_exception(max_retries=3, delay=2)
        def get_ai_content(prompt_text):
            return generate_content(prompt_text)
        
        try:
            response_text = get_ai_content(prompt)
            logger.debug(f"AI response excerpt (first 200 chars): {response_text[:200] if response_text else 'Empty response'}")
        except Exception as e:
            logger.error(f"AI generation failed after retries: {str(e)}")
            return jsonify({
                "error": ERROR_MESSAGES['ai_generation_failed'],
                "message": "Our AI service is currently experiencing issues. Please try again in a few minutes."
            }), 503
        
        try:
            # Parse the AI response to JSON
            quiz_content = parse_ai_json(response_text)
            logger.debug(f"Successfully parsed JSON with keys: {list(quiz_content.keys())}")
            
        except Exception as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Response excerpt: {response_text[:500] if response_text else 'None'}")
            
            # Try again with a simplified prompt
            retry_prompt = f"""
            Generate a simple quiz about "{topic}" with {question_count} multiple-choice questions.
            
            Return ONLY a valid JSON object with this structure:
            {{
              "title": "Quiz on {topic}",
              "description": "Test your knowledge of {topic}.",
              "level": "{level}",
              "questions": [
                {{
                  "question": "Simple question about {topic}?",
                  "options": ["Option A", "Option B", "Option C", "Option D"],
                  "correct_answer": "Option B",
                  "explanation": "Brief explanation of why B is correct."
                }}
              ]
            }}
            
            CRITICAL: Ensure all JSON is properly formatted with all quotes, brackets, and commas.
            """
            
            try:
                response_text = get_ai_content(retry_prompt)
                quiz_content = parse_ai_json(response_text)
                logger.info("Successfully parsed JSON on second attempt with simplified prompt")
                
            except Exception as retry_error:
                logger.error(f"JSON parsing retry failed: {str(retry_error)}")
                return jsonify({
                    "error": "Failed to parse AI response. Please try again later.",
                    "message": "We encountered an issue processing the AI response. Please try again with a simpler topic."
                }), 500
        
        # Validate quiz content
        if not quiz_content or not isinstance(quiz_content, dict):
            return jsonify({
                "error": "Invalid quiz content structure",
                "message": "Failed to generate a valid quiz. Please try again."
            }), 500
            
        required_fields = ['title', 'description', 'questions']
        for field in required_fields:
            if field not in quiz_content:
                return jsonify({
                    "error": f"Missing required field: {field}",
                    "message": "The generated quiz is incomplete. Please try again."
                }), 500
                
        if not isinstance(quiz_content['questions'], list) or not quiz_content['questions']:
            return jsonify({
                "error": "No questions generated",
                "message": "Failed to generate quiz questions. Please try again."
            }), 500
            
        # Remove level field from response if present
        if 'level' in quiz_content:
            del quiz_content['level']
            
        processing_time = time.time() - start_time
        logger.info(f"Successfully generated quiz in {processing_time:.2f}s")
        
        return jsonify(quiz_content), 200
            
    except Exception as e:
        logger.error(f"Unexpected error in generate_quiz: {str(e)}\n{traceback.format_exc()}")
        
        return jsonify({
            "error": ERROR_MESSAGES['server_error'],
            "message": "An unexpected error occurred. Please try again later."
        }), 500