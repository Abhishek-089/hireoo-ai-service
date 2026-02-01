"""
Service for interacting with Google's Gemini API for job info extraction.
"""

import json
import logging
from typing import Dict, Any, List
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google's Gemini API."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.model = None

    async def initialize(self):
        """Initialize the Gemini client."""
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. Gemini service will not function correctly.")
            return

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Gemini service initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")

    async def extract_job_info(self, text: str, spacy_entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract job information from text using Gemini.

        Args:
            text: Cleaned text from the job post
            spacy_entities: Pre-extracted entities from spaCy (used for context)

        Returns:
            Dictionary with extracted job info
        """
        if not self.model:
            logger.error("Gemini model not initialized")
            return {}

        start_time = logging.time.time()

        try:
            # Construct prompt
            prompt = self._construct_prompt(text, spacy_entities)

            # Generate content
            # Set safety settings to be less restrictive for job content
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            }

            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                top_k=40,
                max_output_tokens=1024,
            )
            
            # Using async generation if available or synchronous wrapped in run_in_executor
            # The python SDK is synchronous primarily, but we can call it directly here
            # considering it's an IO bound operation, in a real async app we might want to offload this.
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            result_text = response.text
            
            # Clean up markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            try:
                data = json.loads(result_text)
                return data
            except json.JSONDecodeError:
                logger.error(f"Failed to parse Gemini response as JSON: {result_text[:100]}...")
                return {"error": "Failed to parse JSON response"}
                
        except Exception as e:
            logger.error(f"Gemini extraction failed: {e}")
            return {"error": str(e)}

    def _construct_prompt(self, text: str, spacy_entities: Dict[str, Any]) -> str:
        """Construct the prompt for Gemini."""
        
        # Format spacy entities for context
        entities_str = json.dumps(spacy_entities, indent=2)
        
        # Truncate text if too long (Gemini has large context but good to be safe)
        if len(text) > 15000:
            text = text[:15000] + "...(truncated)"
            
        return f"""
        You are an expert HR data analyst. Your task is to extract structured job information from the raw text of a LinkedIn job post.
        
        I will provide the raw text and some potential entities identified by heuristic rules (spaCy).
        
        Please extract the following fields in strict JSON format:
        - job_title: The specific job title (e.g. "Senior React Developer"). If not explicitly stated, INFER it from the context. Do not use "Unknown".
        - company: The hiring company name. If not explicitly stated, check for email domains or mentions.
        - location: The job location (City, Country or "Remote")
        - skills: A list of specific technical and soft skills required (strings)
        - experience_required: Years of experience or level (e.g. "3-5 years", "Senior")
        - salary_range: Salary information if available (e.g. "$120k - $150k" or "Competitive"), else null
        - job_type: "Full-time", "Part-time", "Contract", "Internship"
        - hr_name: Name of the hiring manager/recruiter if mentioned, else null
        - hr_email: Email address of the recruiter/company if mentioned, else null
        - application_deadline: Date if mentioned, else null
        - description: A clean, formatted summary of the job description in Markdown. 
           - Use paragraphs (\\n\\n) to separate sections like "About the Role", "Requirements", "Benefits". 
           - Do not use headers (#), just bold text (**Role**) if needed.
           - FIX broken lines: Join sentences that are split across lines. 
           - Keep it under 500 words.
        - confidence_score: A float between 0.0 and 1.0 indicating your confidence in the extraction
        
        Raw Text:
        \"\"\"
        {text}
        \"\"\"
        
        Potential Entities (for context only, verify in text):
        {entities_str}
        
        Return ONLY the valid JSON object. Do not include any explanation or markdown formatting outside the JSON.
        """

    async def cleanup(self):
        """Cleanup resources."""
        self.model = None
