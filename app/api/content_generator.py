from flask import Blueprint, request, jsonify
import logging
import time
import traceback
import requests
from app.models.gemini_model import generate_content
from app.utils.helpers import parse_ai_json, validate_tutorial_content, retry_on_exception
from app.config.config import ERROR_MESSAGES, YOUTUBE_API_KEY

content_bp = Blueprint('content', __name__)
logger = logging.getLogger(__name__)

def fetch_youtube_videos(topic, max_results=2):
    """Fetch relevant YouTube videos for a given topic - simplified version"""
    try:
        if not YOUTUBE_API_KEY:
            logger.warning("YouTube API key not configured")
            return []
            
        search_query = f"{topic} tutorial"
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": search_query,
            "type": "video",
            "maxResults": max_results,
            "key": YOUTUBE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=3)  # Add timeout
        if response.status_code != 200:
            logger.error(f"YouTube API error: {response.status_code}")
            return []
            
        data = response.json()
        videos = []
        for item in data.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            videos.append({
                "title": title,
                "url": f"https://www.youtube.com/watch?v={video_id}"
            })
            
        return videos
    except Exception as e:
        logger.error(f"Error fetching YouTube videos: {str(e)}")
        return []  

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
        
        if 'topic' in data:
            topic = data['topic'].strip()
        else:
            return jsonify({"error": ERROR_MESSAGES['missing_fields']}), 400
            
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
            
        format_type = data.get('format', 'tutorial').strip()
        
        logger.info(f"Generating {format_type} content for topic: '{topic}', level: '{level}'")
        
        prompt = f"""
        Create a comprehensive {format_type} about "{topic}" for {level} level learners.
        
        Structure your response with:
        
        # Title
        
        ## Overview
        A brief overview of what this {format_type} covers.
        
        ## About {topic}
        Provide context and background information.
        
        ## Key Sections
        Include 3-5 sections with clear headings, explanations, and simple code examples where relevant.
        
        ## Practice Exercises
        Suggest 2-3 exercises for the learner.
        
        ## Additional Resources
        List helpful resources for further learning.
        
        Use markdown formatting with headings (# and ##), lists (- or *), and code blocks (```language) for clarity.
        Keep code examples simple, avoiding complex syntax or multi-line examples if possible.
        Tailor the content to be appropriate for {level} level learners.
        """
        
        try:
            content = generate_content(prompt, format_type='markdown')
            
            youtube_links = fetch_youtube_videos(topic, max_results=2)
            
            response = {
                "content": content,  
                "youtube_links": youtube_links  
            }
            
            processing_time = time.time() - start_time
            logger.info(f"Successfully generated content in {processing_time:.2f}s")
            
            return jsonify(response), 200
            
        except Exception as e:
            logger.error(f"Content generation error: {str(e)}")
            return jsonify({
                "error": "Failed to generate content",
                "message": "We encountered an issue generating content. Please try again."
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "error": ERROR_MESSAGES['server_error'],
            "message": "An unexpected error occurred. Please try again later."
        }), 500