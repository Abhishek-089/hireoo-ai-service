"""
Main extraction service that orchestrates HTML cleaning, spaCy NER, and OpenAI processing.
"""

import time
import logging
from typing import Dict, Any

from app.services.spacy_service import SpacyService
from app.services.openai_service import OpenAIService
from app.utils.html_cleaner import HTMLCleaner
from app.models.extraction import ExtractedJobInfo

logger = logging.getLogger(__name__)


class ExtractionService:
    """Main service for extracting job information from LinkedIn posts."""

    def __init__(self):
        self.spacy_service = SpacyService()
        self.openai_service = OpenAIService()

    async def initialize(self):
        """Initialize all dependent services."""
        logger.info("Initializing extraction service...")
        await self.spacy_service.initialize()
        logger.info("Extraction service initialized")

    async def extract_job_info(self, raw_html: str, raw_text: str) -> ExtractedJobInfo:
        """
        Extract job information from LinkedIn post data.

        Args:
            raw_html: Raw HTML from LinkedIn post
            raw_text: Raw text content

        Returns:
            Structured job information
        """
        start_time = time.time()

        try:
            logger.info("Starting job information extraction")

            # Step 1: Clean HTML if needed
            cleaned_text = HTMLCleaner.clean_html(raw_html) if raw_html else raw_text

            # Use raw_text if cleaning didn't work well
            if len(cleaned_text) < len(raw_text) * 0.5:
                cleaned_text = raw_text

            logger.debug(f"Cleaned text length: {len(cleaned_text)}")

            # Step 2: Extract entities with spaCy
            spacy_result = await self.spacy_service.extract_entities(cleaned_text)
            logger.debug(f"spaCy entities extracted: {len(spacy_result.get('spacy_entities', {}))}")

            # Step 3: Use OpenAI for intelligent extraction and cleanup
            final_result = await self.openai_service.extract_job_info(cleaned_text, spacy_result)

            # Step 4: Validate and structure the result
            extracted_info = self._structure_result(final_result, spacy_result)

            processing_time = time.time() - start_time
            logger.info(f"Job extraction completed in {processing_time:.2f} seconds")
            return extracted_info

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            processing_time = time.time() - start_time

            # Return minimal result on failure
            return ExtractedJobInfo(
                job_title=None,
                company=None,
                location=None,
                skills=[],
                experience_required=None,
                hr_name=None,
                hr_email=None,
                confidence_score=0.0
            )

    def _structure_result(self, openai_result: Dict[str, Any], spacy_result: Dict[str, Any]) -> ExtractedJobInfo:
        """Structure the extraction result into the expected format."""

        # Extract skills array
        skills = openai_result.get('skills', [])
        if isinstance(skills, str):
            # If OpenAI returned a string, split by commas
            skills = [skill.strip() for skill in skills.split(',') if skill.strip()]

        # Ensure skills is a list
        if not isinstance(skills, list):
            skills = []

        # Extract HR email from patterns if not found by OpenAI
        hr_email = openai_result.get('hr_email')
        if not hr_email:
            patterns = spacy_result.get('patterns', {})
            emails = patterns.get('emails', [])
            if emails:
                hr_email = emails[0]

        return ExtractedJobInfo(
            job_title=openai_result.get('job_title'),
            company=openai_result.get('company'),
            location=openai_result.get('location'),
            skills=skills,
            experience_required=openai_result.get('experience_required'),
            hr_name=openai_result.get('hr_name'),
            hr_email=hr_email,
            salary_range=openai_result.get('salary_range'),
            job_type=openai_result.get('job_type'),
            application_deadline=openai_result.get('application_deadline'),
            confidence_score=openai_result.get('confidence_score', 0.0)
        )

    async def cleanup(self):
        """Cleanup all services."""
        await self.spacy_service.cleanup()
        await self.openai_service.cleanup()
        logger.info("Extraction service cleaned up")

