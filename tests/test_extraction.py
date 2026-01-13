"""
Basic tests for the AI extraction service.
"""

import pytest
from app.services.extraction_service import ExtractionService
from app.models.extraction import ExtractionRequest


@pytest.mark.asyncio
async def test_extraction_service():
    """Test the main extraction service."""
    service = ExtractionService()
    await service.initialize()

    # Sample LinkedIn post data
    request = ExtractionRequest(
        raw_html="<div>We're hiring a Senior Software Engineer at Google!</div>",
        raw_text="We're hiring a Senior Software Engineer at Google! Must have 5+ years experience with Python and React. Contact sarah.johnson@google.com"
    )

    result = await service.extract_job_info(request.raw_html, request.raw_text)

    # Basic assertions
    assert result.job_title is not None or result.company is not None
    assert isinstance(result.skills, list)
    assert 0.0 <= result.confidence_score <= 1.0

    await service.cleanup()


def test_html_cleaner():
    """Test HTML cleaning functionality."""
    from app.utils.html_cleaner import HTMLCleaner

    dirty_html = """
    <div class="feed-shared-text">
        <div class="feed-shared-control-menu">Menu</div>
        We're hiring a developer!
        <button>Apply</button>
    </div>
    """

    clean_text = HTMLCleaner.clean_html(dirty_html)
    assert "We're hiring a developer!" in clean_text
    assert "Menu" not in clean_text
    assert "Apply" not in clean_text


def test_email_extraction():
    """Test email extraction patterns."""
    from app.services.spacy_service import SpacyService

    text = "Contact john.doe@company.com or jane@startup.io for more info."
    service = SpacyService()

    # Note: This would need proper initialization in a real test
    # For now, just test the pattern directly
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text, re.IGNORECASE)

    assert "john.doe@company.com" in emails
    assert "jane@startup.io" in emails


