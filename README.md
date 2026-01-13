# Hireoo AI Extraction Service

FastAPI microservice for extracting job information from LinkedIn posts using spaCy NER and OpenAI.

## Features

- 🧠 **spaCy NER**: Named Entity Recognition for extracting persons, organizations, locations
- 🤖 **OpenAI Integration**: Intelligent job information extraction and cleanup
- 🧹 **HTML Cleaning**: Convert LinkedIn post HTML to clean, readable text
- 📧 **Email Extraction**: Regex-based email address detection
- 🔄 **Batch Processing**: Process multiple posts simultaneously
- 🐳 **Docker Ready**: Containerized deployment with health checks

## API Endpoints

### POST `/api/v1/extract`

Extract job information from a single LinkedIn post.

**Request:**
```json
{
  "raw_html": "<div>We're hiring a Senior Software Engineer!</div>",
  "raw_text": "We're hiring a Senior Software Engineer! Apply now at google.com/careers"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_title": "Senior Software Engineer",
    "company": "Google",
    "location": "Mountain View, CA",
    "skills": ["Python", "JavaScript", "React"],
    "experience_required": "5+ years",
    "hr_name": "Sarah Johnson",
    "hr_email": "sarah.johnson@google.com",
    "salary_range": "$150,000 - $200,000",
    "job_type": "Full-time",
    "confidence_score": 0.92
  },
  "processing_time": 2.34
}
```

### POST `/api/v1/extract/batch`

Process multiple posts in a single request (max 10 posts).

**Request:**
```json
[
  {
    "raw_html": "<div>Post 1 HTML...</div>",
    "raw_text": "Post 1 text..."
  },
  {
    "raw_html": "<div>Post 2 HTML...</div>",
    "raw_text": "Post 2 text..."
  }
]
```

### GET `/api/v1/health`

Service health check and status.

## Installation & Setup

### Prerequisites

- Python 3.11+
- OpenAI API key
- Docker (optional)

### Local Development

1. **Clone and navigate:**
   ```bash
   cd ai-service
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model:**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Set environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

6. **Run the service:**
   ```bash
   python -m app.main
   ```

### Docker Deployment

1. **Build the image:**
   ```bash
   docker build -t hireoo-ai-service .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 --env-file .env hireoo-ai-service
   ```

## Architecture

### Core Components

```
app/
├── main.py              # FastAPI application entry point
├── core/
│   ├── config.py        # Settings and configuration
│   └── logging.py       # Logging setup
├── models/
│   └── extraction.py    # Pydantic models for API
├── services/
│   ├── extraction_service.py    # Main orchestration service
│   ├── spacy_service.py         # spaCy NER processing
│   └── openai_service.py        # OpenAI API integration
├── utils/
│   └── html_cleaner.py          # HTML cleaning utilities
└── api/
    └── v1/
        └── routes.py            # API route definitions
```

### Processing Pipeline

1. **HTML Cleaning**: Remove LinkedIn UI elements and extract readable text
2. **spaCy NER**: Extract named entities (persons, organizations, locations)
3. **Pattern Matching**: Regex-based extraction for emails, salaries, experience
4. **OpenAI Processing**: Intelligent structuring and cleanup of extracted data
5. **Validation**: Ensure extracted data meets quality standards

## Configuration

### Environment Variables

```env
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.1

# spaCy Configuration
SPACY_MODEL=en_core_web_sm

# Processing Limits
MAX_TEXT_LENGTH=10000
REQUEST_TIMEOUT=30
```

## Usage Examples

### Python Client

```python
import requests

# Single post extraction
response = requests.post("http://localhost:8000/api/v1/extract", json={
    "raw_html": "<div>We're hiring!</div>",
    "raw_text": "We're hiring a Senior Developer"
})

result = response.json()
print(result["data"]["job_title"])  # "Senior Developer"
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_html": "<div>Hiring now!</div>",
    "raw_text": "Senior Software Engineer position available"
  }'
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black app/
isort app/
```

### API Documentation

When running locally, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Production Deployment

### Docker Compose Example

```yaml
version: '3.8'
services:
  ai-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Environment Considerations

- **Memory**: spaCy models require ~500MB RAM
- **API Limits**: Monitor OpenAI API usage and costs
- **Rate Limiting**: Implement request rate limiting for production
- **Caching**: Consider caching for repeated extractions

## Monitoring & Logging

- **Health Checks**: `/health` endpoint for service monitoring
- **Structured Logging**: JSON-formatted logs with request IDs
- **Performance Metrics**: Processing time tracking per request
- **Error Tracking**: Comprehensive error logging and handling

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update API documentation
4. Ensure all dependencies are properly declared

## License

This service is part of the Hireoo platform.


