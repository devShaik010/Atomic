from flask import Blueprint, request, jsonify
import logging
import time
import traceback
from app.models.gemini_model import generate_content
from app.utils.helpers import parse_ai_json, validate_tutorial_content, retry_on_exception
from app.config.config import ERROR_MESSAGES

content_bp = Blueprint('content', __name__)
logger = logging.getLogger(__name__)

@content_bp.route('/generate-content', methods=['POST'])
def generate_tutorial_content():
    start_time = time.time()
    
    try:
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": ERROR_MESSAGES['invalid_json']}), 400
        except Exception:
            return jsonify({"error": ERROR_MESSAGES['invalid_json']}), 400
        
        if not data or 'topic' not in data or 'level' not in data:
            return jsonify({"error": ERROR_MESSAGES['missing_fields']}), 400
            
        topic = data['topic'].strip()
        level = data['level'].strip()
        format_type = data.get('format', 'tutorial').strip()
        
        logger.info(f"Generating {format_type} content for topic: '{topic}', level: '{level}'")
        
        prompt = f"""
        Generate a structured {format_type} about "{topic}" for a {level} level learner.

        The response should be in valid JSON format with the following structure:
        {{
          "title": "Understanding JavaScript Promises",
          "level": "Intermediate",
          "estimated_time": "15 minutes",
          "overview": "This tutorial explains how JavaScript Promises work and how to use them effectively for asynchronous operations.",
          "prerequisites": ["Basic JavaScript knowledge", "Understanding of callbacks"],
          "sections": [
            {{
              "section_title": "What are Promises?",
              "content": "Promises in JavaScript represent the eventual completion (or failure) of an asynchronous operation and its resulting value.",
              "code_example": "console.log('Simple example');"
            }}
          ],
          "practice_exercises": [
            "Create a Promise that resolves after a random time between 1-3 seconds"
          ],
          "additional_resources": [
            {{
              "title": "MDN Web Docs: Promise",
              "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise"
            }}
          ]
        }}

        Make sure to include:
        1. A descriptive title related to the topic
        2. The correct level as provided in the input
        3. A realistic estimated time to complete the tutorial
        4. A concise but informative overview
        5. Relevant prerequisites for understanding the content
        6. At least 3-5 detailed sections with explanations and code examples where appropriate
        7. Practice exercises for the learner
        8. Additional resources for further learning

        CRITICAL FORMATTING INSTRUCTIONS:
        - Ensure all JSON is properly formatted and valid
        - For code examples:
          - KEEP THEM VERY SIMPLE to avoid escaping issues
          - Use simple, basic examples without complex syntax
          - Avoid multi-line code examples if possible
          - Do not include docstrings, decorators, or complex functions in examples
          - Use \\n instead of actual newlines if you must include multi-line code
        - Do NOT use backticks, markdown formatting, or code blocks in your response
        - Return ONLY the JSON object with no explanations outside the JSON

        The content should be comprehensive, accurate, and tailored to the specified level.
        """
        
        # Use retry mechanism for AI generation
        @retry_on_exception(max_retries=3, delay=2)
        def get_ai_content(prompt_text):
            return generate_content(prompt_text)
        
        try:
            response_text = get_ai_content(prompt)
            # Log a sample of the response for debugging
            logger.debug(f"AI response excerpt (first 200 chars): {response_text[:200] if response_text else 'Empty response'}")
        except Exception as e:
            logger.error(f"AI generation failed after retries: {str(e)}")
            return jsonify({
                "error": ERROR_MESSAGES['ai_generation_failed'],
                "message": "Our AI service is currently experiencing issues. Please try again in a few minutes."
            }), 503
        
        try:
            # Log the full response to help with debugging
            logger.debug("Full AI response:")
            logger.debug("-" * 80)
            logger.debug(response_text)
            logger.debug("-" * 80)
            
            # Use the improved parse_ai_json function to handle edge cases
            tutorial_content = parse_ai_json(response_text)
            
            # Log the parsed structure to verify success
            logger.debug(f"Successfully parsed JSON with keys: {list(tutorial_content.keys())}")
            
        except Exception as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Response excerpt: {response_text[:500] if response_text else 'None'}")
            
            # Try again with a direct approach - this is a fallback measure
            try:
                # Modify the prompt to be more explicit about JSON formatting
                retry_prompt = f"""
                Generate a simple and clean {format_type} about "{topic}" for a {level} level learner.
                
                Return ONLY a valid JSON object with this structure:
                {{
                  "title": "Simple title",
                  "level": "{level}",
                  "estimated_time": "15-30 minutes",
                  "overview": "Brief overview of the topic.",
                  "prerequisites": ["Basic knowledge"],
                  "sections": [
                    {{
                      "section_title": "Introduction",
                      "content": "Simple explanation without complex code."
                    }},
                    {{
                      "section_title": "Key Concepts",
                      "content": "Basic information about the topic."
                    }}
                  ],
                  "practice_exercises": ["Simple practice exercise"],
                  "additional_resources": [{{ "title": "Resource", "url": "https://example.com" }}]
                }}
                
                CRITICAL: Ensure all JSON is properly formatted with all quotes, brackets, and commas. Do not use any code examples with special characters.
                """
                
                response_text = get_ai_content(retry_prompt)
                tutorial_content = parse_ai_json(response_text)
                logger.info("Successfully parsed JSON on second attempt with simplified prompt")
                
            except Exception as retry_error:
                logger.error(f"JSON parsing retry failed: {str(retry_error)}")
                return jsonify({
                    "error": "Failed to parse AI response. Please try again later.",
                    "message": "We encountered an issue processing the AI response. Please try again with a simpler topic."
                }), 500
        
        # Use the relaxed validation function
        is_valid, validation_error = validate_tutorial_content(tutorial_content)
        if not is_valid:
            logger.warning(f"Invalid tutorial content structure: {validation_error}\nContent keys: {list(tutorial_content.keys())}")
            
            # Attempt to fix common issues
            if 'prerequisites' in tutorial_content and not tutorial_content['prerequisites']:
                tutorial_content['prerequisites'] = ["Basic knowledge of the subject"]
                
            if 'practice_exercises' in tutorial_content and not tutorial_content['practice_exercises']:
                tutorial_content['practice_exercises'] = ["Practice implementing the concepts covered in this tutorial"]
                
            # Re-validate after fixes
            is_valid, _ = validate_tutorial_content(tutorial_content)
            
            if not is_valid:
                return jsonify({
                    "error": "Generated content is incomplete",
                    "message": f"Please try again. Issue: {validation_error}"
                }), 500
        
        def sanitize_tutorial_content(content):
            """Sanitize and ensure all code examples are properly formatted"""
            if not content or not isinstance(content, dict):
                return content
            
            # Make a copy to avoid modifying the original
            result = content.copy()
            
            # Process sections to sanitize code examples
            if 'sections' in result and isinstance(result['sections'], list):
                for section in result['sections']:
                    if isinstance(section, dict) and 'code_example' in section:
                        # Replace problematic code examples with simplified versions
                        if len(section['code_example']) > 200:
                            # If code is too long, simplify it
                            section['code_example'] = "# Simplified example\nprint('Example code')"
                        
                        # Ensure code example is properly escaped
                        section['code_example'] = section['code_example'].replace('\n', '\\n')
            
            return result

        tutorial_content = sanitize_tutorial_content(tutorial_content)
        processing_time = time.time() - start_time
        logger.info(f"Successfully generated tutorial content in {processing_time:.2f}s")
        
        return jsonify(tutorial_content), 200
            
    except Exception as e:
        logger.error(f"Unexpected error in generate_tutorial_content: {str(e)}\n{traceback.format_exc()}")
        
        return jsonify({
            "error": ERROR_MESSAGES['server_error'],
            "message": "An unexpected error occurred. Please try again later."
        }), 500