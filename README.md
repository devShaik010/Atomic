# Atomic API Documentation

## API Endpoints

### `/generate-roadmap`
Generates a structured learning roadmap based on user inputs.

**Method**: POST

**Request Body Format**:
```json
{
  "topic": "string",      // e.g., "Machine Learning", "Web Development"
  "level": "string",      // e.g., "Beginner", "Intermediate", "Advanced"
  "timeframe": "string"   // e.g., "2 weeks", "3 months"
}
```

**Response**: JSON object containing the generated roadmap structure

### `/generate-content`
Creates detailed content for specific topics within a roadmap.

**Method**: POST

**Request Body Format**:
```json
{
  "topic": "string",     // Specific topic to generate content for
  "depth": "string"      // e.g., "Overview", "Comprehensive"
}
```

**Response**: JSON object containing the generated educational content