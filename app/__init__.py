import logging
from flask import Flask, jsonify

def create_app():
    app = Flask(__name__)
    
    from app.config.config import ENV
    app.config.update(
        ENV=ENV,
        DEBUG=ENV == 'development',
        JSON_SORT_KEYS=False,
        MAX_CONTENT_LENGTH=1 * 1024 * 1024
    )
    
    from app.utils.middleware import setup_middleware
    setup_middleware(app)
    
    from app.api.roadmap_generator import roadmap_bp
    from app.api.content_generator import content_bp
    
    app.register_blueprint(roadmap_bp, url_prefix='/api')
    app.register_blueprint(content_bp, url_prefix='/api')
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "ok", "version": "1.0.0"}), 200
    
    return app
