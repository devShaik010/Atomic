import time
import logging
import traceback
from flask import request, jsonify
from werkzeug.exceptions import HTTPException
from app.config.config import RATE_LIMIT_WINDOW, MAX_REQUESTS_PER_WINDOW, ERROR_MESSAGES

logger = logging.getLogger(__name__)
request_timestamps = {}

def setup_middleware(app):
    @app.before_request
    def before_request():
        logger.info(f"Request: {request.method} {request.path} - {request.remote_addr}")
        client_ip = request.remote_addr
        current_time = time.time()
        
        for ip in list(request_timestamps.keys()):
            timestamps = request_timestamps[ip]
            request_timestamps[ip] = [ts for ts in timestamps if current_time - ts < RATE_LIMIT_WINDOW]
            if not request_timestamps[ip]:
                del request_timestamps[ip]
        
        if client_ip in request_timestamps:
            if len(request_timestamps[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
                logger.warning(f"Rate limit exceeded for {client_ip}")
                return jsonify({
                    "error": ERROR_MESSAGES['rate_limit'],
                    "retry_after": RATE_LIMIT_WINDOW - (current_time - min(request_timestamps[client_ip]))
                }), 429
            
            request_timestamps[client_ip].append(current_time)
        else:
            request_timestamps[client_ip] = [current_time]

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {str(e)}\n{traceback.format_exc()}")
        
        if isinstance(e, HTTPException):
            return jsonify({
                "error": e.description,
                "status_code": e.code
            }), e.code
        
        return jsonify({
            "error": ERROR_MESSAGES['server_error'],
            "message": "Please try again later"
        }), 500
