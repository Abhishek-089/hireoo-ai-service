"""
OpenAI service for intelligent job information extraction and cleanup.
"""

import openai
from typing import Dict, Any, Optional
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for using OpenAI API to extract and structure job information."""

    def __init__(self):
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client."""
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if api_key and api_key.strip() and api_key != 'your-openai-api-key-here':
            try:
                self.client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("OpenAI API key not configured - AI extraction features will be limited")
            self.client = None

    async def extract_job_info(self, raw_text: str, spacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use OpenAI to intelligently extract and structure job information.

        Args:
            raw_text: The cleaned text from the LinkedIn post
            spacy_data: Pre-extracted entities from spaCy

        Returns:
            Structured job information
        """
        if not self.client:
            logger.warning("OpenAI client not available, returning spaCy data only")
            return self._fallback_extraction(spacy_data)

        try:
            prompt = self._build_extraction_prompt(raw_text, spacy_data)

            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting job posting information from social media posts. Extract structured information accurately and return it as valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
            )

            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("Empty response from OpenAI")

            # Parse JSON response
            try:
                extracted_data = json.loads(result_text)
                extracted_data['confidence_score'] = self._calculate_confidence(extracted_data)
                return extracted_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                logger.error(f"OpenAI response: {result_text}")
                return self._fallback_extraction(spacy_data)

        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}")
            return self._fallback_extraction(spacy_data)

    def _build_extraction_prompt(self, raw_text: str, spacy_data: Dict[str, Any]) -> str:
        """Build the prompt for OpenAI."""

        return f"""
Extract job posting information from this LinkedIn post. Return a JSON object with the following fields:

- job_title: The specific job title being offered
- company: The company name
- location: Where the job is located (city, state, remote, etc.)
- skills: Array of required technical skills and qualifications
- experience_required: Experience level or years required
- hr_name: Name of the HR contact person (if mentioned)
- hr_email: Email address of the HR contact (if visible)
- salary_range: Salary information if mentioned
- job_type: Employment type (full-time, part-time, contract, internship)
- application_deadline: Any mentioned deadline for applications

Only include fields that are clearly mentioned or strongly implied. If information is not available, use null for single values or empty arrays for lists.

LinkedIn Post Text:
{raw_text}

Pre-extracted Entities (for reference):
{json.dumps(spacy_data, indent=2)}

Return only valid JSON, no additional text or explanation.
"""

    def _calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted data completeness."""
        required_fields = ['job_title', 'company']
        optional_fields = ['location', 'skills', 'experience_required', 'hr_name', 'hr_email']

        # Check required fields
        required_present = sum(1 for field in required_fields if extracted_data.get(field))
        required_score = required_present / len(required_fields)

        # Check optional fields
        optional_present = sum(1 for field in optional_fields if extracted_data.get(field))
        optional_score = optional_present / len(optional_fields)

        # Weighted score
        confidence = (required_score * 0.7) + (optional_score * 0.3)

        return round(confidence, 2)

    def _fallback_extraction(self, spacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback extraction using spaCy data when OpenAI is unavailable."""
        entities = spacy_data.get('spacy_entities', {})
        patterns = spacy_data.get('patterns', {})

        # Extract basic information from spaCy entities
        job_title = None
        company = None
        location = None

        # Try to identify company from organizations
        orgs = entities.get('organizations', [])
        if orgs:
            company = orgs[0]['text']

        # Try to identify location
        locations = entities.get('locations', [])
        if locations:
            location = locations[0]['text']

        # Extract emails
        emails = patterns.get('emails', [])
        hr_email = emails[0] if emails else None

        # Extract skills (this would need more sophisticated logic)
        skills = []
        experience_patterns = patterns.get('experience_patterns', [])
        experience_required = experience_patterns[0] if experience_patterns else None

        return {
            'job_title': job_title,
            'company': company,
            'location': location,
            'skills': skills,
            'experience_required': experience_required,
            'hr_name': None,
            'hr_email': hr_email,
            'salary_range': None,
            'job_type': None,
            'application_deadline': None,
            'confidence_score': 0.3,  # Lower confidence for fallback
        }

    async def cleanup(self):
        """Cleanup resources."""
        if self.client:
            # OpenAI client cleanup if needed
            pass

