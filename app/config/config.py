import os
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv('FLASK_ENV', 'development')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1024,
}

MAX_RETRIES = 3
RETRY_DELAY = 2

ERROR_MESSAGES = {
    'missing_fields': 'Missing required fields in request',
    'invalid_json': 'Invalid JSON in request body',
    'ai_generation_failed': 'Failed to generate content. Please try again later.',
    'json_parse_error': 'Failed to parse AI response. Please try again later.',
    'server_error': 'An unexpected error occurred. Please try again later.',
    'rate_limit': 'Rate limit exceeded. Please try again later.',
    'service_unavailable': 'Service temporarily unavailable. Please try again later.',
}

RATE_LIMIT_WINDOW = 60
MAX_REQUESTS_PER_WINDOW = 10
