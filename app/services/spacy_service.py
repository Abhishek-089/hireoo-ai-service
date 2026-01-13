"""
spaCy-based Named Entity Recognition service for job information extraction.
"""

import spacy
from spacy.lang.en import English
from typing import Dict, List, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class SpacyService:
    """Service for extracting entities from job post text using spaCy."""

    def __init__(self):
        self.nlp: Optional[spacy.language.Language] = None
        self.sentencizer = None

    async def initialize(self):
        """Initialize spaCy model."""
        try:
            # Load spaCy model
            self.nlp = spacy.load("en_core_web_sm")

            # Add sentencizer for better sentence segmentation
            self.sentencizer = self.nlp.add_pipe("sentencizer")

            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.warning("spaCy model not found, downloading...")
            # Download model if not available
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
            self.sentencizer = self.nlp.add_pipe("sentencizer")
            logger.info("spaCy model downloaded and loaded")

    async def extract_entities(self, text: str) -> Dict[str, any]:
        """
        Extract named entities from text using spaCy.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary with extracted entities
        """
        if not self.nlp:
            raise RuntimeError("spaCy model not initialized")

        try:
            # Process text
            doc = self.nlp(text)

            # Extract different entity types
            entities = {
                'persons': self._extract_entities_by_label(doc, 'PERSON'),
                'organizations': self._extract_entities_by_label(doc, 'ORG'),
                'locations': self._extract_entities_by_label(doc, 'GPE', 'LOC'),
                'money': self._extract_entities_by_label(doc, 'MONEY'),
                'dates': self._extract_entities_by_label(doc, 'DATE'),
            }

            # Extract additional patterns
            patterns = self._extract_patterns(text)

            return {
                'spacy_entities': entities,
                'patterns': patterns,
                'confidence': self._calculate_confidence(doc, entities),
            }

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {
                'spacy_entities': {
                    'persons': [],
                    'organizations': [],
                    'locations': [],
                    'money': [],
                    'dates': [],
                },
                'patterns': {},
                'confidence': 0.0,
            }

    def _extract_entities_by_label(self, doc: spacy.tokens.Doc, *labels: str) -> List[Dict[str, any]]:
        """Extract entities by label."""
        entities = []

        for ent in doc.ents:
            if ent.label_ in labels:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': getattr(ent, '_.confidence', 1.0),  # spaCy 3.0+ confidence
                })

        return entities

    def _extract_patterns(self, text: str) -> Dict[str, List[str]]:
        """Extract additional patterns not covered by spaCy NER."""

        patterns = {
            'emails': self._extract_emails(text),
            'phone_numbers': self._extract_phone_numbers(text),
            'experience_patterns': self._extract_experience_patterns(text),
            'job_titles': self._extract_job_title_patterns(text),
            'salary_patterns': self._extract_salary_patterns(text),
        }

        return patterns

    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text, re.IGNORECASE)

    def _extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers."""
        # Basic phone pattern - can be enhanced
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        return re.findall(phone_pattern, text)

    def _extract_experience_patterns(self, text: str) -> List[str]:
        """Extract experience requirements."""
        experience_patterns = [
            r'(\d+\+?\s*years?\s*(?:of\s*)?experience)',
            r'(entry[- ]level)',
            r'(junior|mid|senior|lead|principal)',
            r'(experienced?\s+in)',
        ]

        matches = []
        for pattern in experience_patterns:
            matches.extend(re.findall(pattern, text, re.IGNORECASE))

        return list(set(matches))  # Remove duplicates

    def _extract_job_title_patterns(self, text: str) -> List[str]:
        """Extract potential job titles."""
        # Common job title patterns
        title_patterns = [
            r'\b(?:senior|junior|lead|principal|staff)\s+(?:software|frontend|backend|full.?stack|devops|product|data|machine learning|ai|ux|ui)\s+(?:engineer|developer|manager|scientist|designer)\b',
            r'\b(?:software|frontend|backend|full.?stack|devops|product|data|machine learning|ai|ux|ui)\s+(?:engineer|developer|manager|scientist|designer)\b',
        ]

        matches = []
        for pattern in title_patterns:
            matches.extend(re.findall(pattern, text, re.IGNORECASE))

        return list(set(matches))

    def _extract_salary_patterns(self, text: str) -> List[str]:
        """Extract salary information."""
        salary_patterns = [
            r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:-|to|–)\s*\$[\d,]+(?:\.\d{2})?)?(?:\s*(?:per|\/)\s*(?:year|month|hour|hr))?',
            r'[\d,]+(?:\.\d{2})?\s*(?:-|to|–)\s*[\d,]+(?:\.\d{2})?\s*(?:per|\/)\s*(?:year|month|hour|hr)',
        ]

        matches = []
        for pattern in salary_patterns:
            matches.extend(re.findall(pattern, text, re.IGNORECASE))

        return list(set(matches))

    def _calculate_confidence(self, doc: spacy.tokens.Doc, entities: Dict) -> float:
        """Calculate overall confidence in entity extraction."""
        if not entities:
            return 0.0

        # Simple confidence calculation based on entity coverage
        total_entities = sum(len(entity_list) for entity_list in entities.values())
        if total_entities == 0:
            return 0.0

        # Base confidence on number of entities and text length
        text_length = len(doc.text)
        entity_coverage = total_entities / max(text_length / 100, 1)  # entities per 100 chars

        # Normalize to 0-1 scale
        confidence = min(entity_coverage * 2, 1.0)

        return round(confidence, 2)

    async def cleanup(self):
        """Cleanup resources."""
        if self.nlp:
            # spaCy cleanup if needed
            pass


