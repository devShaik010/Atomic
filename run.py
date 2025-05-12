import os
import logging
from app import create_app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    ENV = os.getenv('FLASK_ENV', 'development')
    if ENV == 'production':
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
    else:
        app.run(debug=True, port=5000)
