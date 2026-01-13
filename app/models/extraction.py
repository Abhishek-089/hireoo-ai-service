"""
Pydantic models for the extraction API.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum


class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class ExtractionRequest(BaseModel):
    """Request model for job extraction."""

    raw_html: str = Field(..., description="Raw HTML content from LinkedIn post")
    raw_text: str = Field(..., description="Clean text content from LinkedIn post")

    @validator('raw_html', 'raw_text')
    def validate_content_length(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Content cannot be empty')
        if len(v) > 50000:  # 50KB limit
            raise ValueError('Content too large (max 50KB)')
        return v

    class Config:
        schema_extra = {
            "example": {
                "raw_html": "<div>We're hiring a Senior Software Engineer at Google!</div>",
                "raw_text": "We're hiring a Senior Software Engineer at Google! Apply now at google.com/careers"
            }
        }


class ExtractedJobInfo(BaseModel):
    """Extracted job information."""

    job_title: Optional[str] = Field(None, description="Extracted job title")
    company: Optional[str] = Field(None, description="Company name")
    location: Optional[str] = Field(None, description="Job location")
    skills: List[str] = Field(default_factory=list, description="Required skills")
    experience_required: Optional[str] = Field(None, description="Experience level required")
    hr_name: Optional[str] = Field(None, description="HR contact name")
    hr_email: Optional[str] = Field(None, description="HR contact email")

    salary_range: Optional[str] = Field(None, description="Salary information if mentioned")
    job_type: Optional[str] = Field(None, description="Full-time, part-time, contract, etc.")
    application_deadline: Optional[str] = Field(None, description="Application deadline if mentioned")

    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="AI confidence in extraction")

    class Config:
        schema_extra = {
            "example": {
                "job_title": "Senior Software Engineer",
                "company": "Google",
                "location": "Mountain View, CA",
                "skills": ["Python", "JavaScript", "React", "Node.js"],
                "experience_required": "5+ years",
                "hr_name": "Sarah Johnson",
                "hr_email": "sarah.johnson@google.com",
                "salary_range": "$150,000 - $200,000",
                "job_type": "Full-time",
                "confidence_score": 0.92
            }
        }


class ExtractionResponse(BaseModel):
    """Response model for extraction API."""

    success: bool = Field(..., description="Whether extraction was successful")
    data: Optional[ExtractedJobInfo] = Field(None, description="Extracted job information")
    error: Optional[str] = Field(None, description="Error message if extraction failed")
    processing_time: float = Field(..., description="Time taken for processing in seconds")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "job_title": "Senior Software Engineer",
                    "company": "Google",
                    "location": "Mountain View, CA",
                    "skills": ["Python", "JavaScript", "React"],
                    "experience_required": "5+ years",
                    "hr_name": "Sarah Johnson",
                    "hr_email": "sarah.johnson@google.com",
                    "confidence_score": 0.92
                },
                "processing_time": 2.34
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    models_loaded: List[str] = Field(..., description="Loaded AI models")
    uptime: float = Field(..., description="Service uptime in seconds")


