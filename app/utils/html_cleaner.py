"""
HTML cleaning utilities for LinkedIn post content.
"""

import re
from bs4 import BeautifulSoup
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class HTMLCleaner:
    """Clean and extract readable text from LinkedIn post HTML."""

    # LinkedIn specific elements to remove
    LINKEDIN_NOISE_SELECTORS = [
        # Social interaction elements
        '[data-test-id="social-counts"]',
        '[data-test-id="social-actions"]',
        '[data-test-id="feed-shared-control-menu"]',
        '.feed-shared-control-menu',

        # Author info that's not relevant
        '[data-test-id="profile-photo"]',
        '.feed-shared-actor__image',
        '.feed-shared-actor__meta',

        # LinkedIn UI elements
        '.feed-shared-social-counts',
        '.feed-shared-social-actions',
        '.feed-shared-control-menu__trigger',

        # Emojis and special characters that might interfere
        '.emoji-unicode',

        # Advertisement elements
        '[data-test-id*="ad"]',
        '.ad-banner',

        # Generic UI elements
        'script',
        'style',
        'noscript',
        'svg',
        'button',
        'form',
    ]

    # Text patterns to clean
    CLEANUP_PATTERNS = [
        (r'\n+', '\n'),  # Multiple newlines to single
        (r'\s+', ' '),   # Multiple spaces to single
        (r'^\s+', ''),   # Leading whitespace
        (r'\s+$', ''),   # Trailing whitespace
        (r'•', '-'),     # Bullet points
        (r'…', '...'),   # Ellipsis
    ]

    @staticmethod
    def clean_html(raw_html: str) -> str:
        """
        Clean HTML content and extract readable text.

        Args:
            raw_html: Raw HTML from LinkedIn post

        Returns:
            Clean, readable text
        """
        if not raw_html or not raw_html.strip():
            return ""

        try:
            # Parse HTML
            soup = BeautifulSoup(raw_html, 'html.parser')

            # Remove noise elements
            for selector in HTMLCleaner.LINKEDIN_NOISE_SELECTORS:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        element.decompose()
                except Exception as e:
                    logger.warning(f"Failed to remove selector {selector}: {e}")

            # Extract text content
            text = soup.get_text(separator='\n', strip=True)

            # Apply cleanup patterns
            for pattern, replacement in HTMLCleaner.CLEANUP_PATTERNS:
                text = re.sub(pattern, replacement, text)

            # Final cleanup
            text = text.strip()

            # Validate result
            if not text or len(text) < 10:
                logger.warning("Extracted text too short or empty")
                return raw_html  # Fallback to original if cleaning fails

            return text

        except Exception as e:
            logger.error(f"Failed to clean HTML: {e}")
            return raw_html  # Fallback to original

    @staticmethod
    def extract_post_metadata(raw_html: str) -> dict:
        """
        Extract additional metadata from LinkedIn post HTML.

        Args:
            raw_html: Raw HTML from LinkedIn post

        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            'has_images': False,
            'has_links': False,
            'has_video': False,
            'word_count': 0,
            'character_count': 0,
        }

        try:
            soup = BeautifulSoup(raw_html, 'html.parser')

            # Check for media content
            metadata['has_images'] = bool(soup.find_all(['img', 'picture']))
            metadata['has_video'] = bool(soup.find_all(['video', 'iframe']))
            metadata['has_links'] = bool(soup.find_all('a', href=True))

            # Get text statistics
            text = soup.get_text()
            metadata['word_count'] = len(text.split()) if text else 0
            metadata['character_count'] = len(text) if text else 0

        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")

        return metadata

    @staticmethod
    def is_job_post(text: str) -> bool:
        """
        Basic check if the text appears to be a job posting.

        Args:
            text: Cleaned text content

        Returns:
            True if likely a job post
        """
        job_keywords = [
            'hiring', 'hiring now', 'we\'re hiring', 'we are hiring',
            'looking for', 'seeking', 'recruiting', 'join our team',
            'open position', 'career opportunity', 'job opening',
            'vacancy', 'positions available', 'talent acquisition',
            'growing team', 'expand'
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in job_keywords)


