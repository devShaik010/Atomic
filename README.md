# Course Roadmap Generator API

A Flask-based API that generates structured course roadmaps using Gemini AI.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file with:
```
GEMINI_API_KEY=your_api_key_here
```

3. Run the application:
```bash
python app.py
```

## API Endpoints

### POST /api/generate-roadmap
Generate a course roadmap

Request Body:
```json
{
  "course_title": "string",
  "level": "string"
}
```

Response:
```json
{
  "course_title": "string",
  "description": "string",
  "level": "string",
  "duration": "string",
  "modules": [
    {
      "module_title": "string",
      "topics": ["string"]
    }
  ]
}
```
