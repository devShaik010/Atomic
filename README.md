# Course Roadmap Generator API

A Flask-based API that generates structured course roadmaps using Google's Gemini AI.

## Features

- Generates comprehensive course roadmaps based on course title and level
- Production-ready with error handling, rate limiting, and logging
- Modular architecture for easy maintenance and extension

## Local Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with:
```
GEMINI_API_KEY=your_api_key_here
FLASK_ENV=development  # or production
```

4. Run the application:
```bash
python run.py
```

## API Endpoints

### POST /api/generate-roadmap
Generate a course roadmap

Request Body:
```json
{
  "course_title": "Frontend Developer",
  "level": "Beginner"
}
```

Response:
```json
{
  "course_title": "Frontend Developer",
  "description": "Learn how to build modern, responsive websites using HTML, CSS, and JavaScript.",
  "level": "Beginner",
  "duration": "3 months",
  "modules": [
    {
      "module_title": "Introduction to Web",
      "topics": ["How the Web Works", "Browsers and Servers", "HTTP Basics"]
    },
    {
      "module_title": "HTML Basics",
      "topics": ["HTML Tags", "Forms", "Semantic HTML"]
    }
  ]
}
```

### GET /health
Health check endpoint

Response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Deployment on Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the service:
   - **Name**: course-roadmap-api (or your preferred name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --config gunicorn_config.py "app:create_app()"`
4. Add environment variables:
   - `GEMINI_API_KEY`: Your Gemini API key
   - `FLASK_ENV`: production
5. Click "Create Web Service"

## Project Structure

```
/
├── app/                  # Application package
│   ├── __init__.py       # App factory
│   ├── api/              # API endpoints
│   │   └── roadmap_generator.py
│   ├── config/           # Configuration
│   │   └── config.py
│   ├── models/           # AI model integration
│   │   └── gemini_model.py
│   └── utils/            # Utilities
│       ├── helpers.py
│       └── middleware.py
├── gunicorn_config.py    # Gunicorn configuration
├── Procfile              # Process file for deployment
├── requirements.txt      # Dependencies
└── run.py                # Application entry point
```
