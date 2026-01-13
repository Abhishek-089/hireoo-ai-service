"""
API routes for the AI extraction service.
"""

import time
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from app.models.extraction import (
    ExtractionRequest,
    ExtractionResponse,
    HealthResponse
)
from app.services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_extraction_service() -> ExtractionService:
    """Dependency to get the extraction service instance."""
    # This would normally be injected via dependency injection
    # For now, we'll create a new instance
    service = ExtractionService()
    return service


@router.post("/extract", response_model=ExtractionResponse)
async def extract_job_info(
    request: ExtractionRequest,
    service: ExtractionService = Depends(get_extraction_service)
) -> ExtractionResponse:
    """
    Extract job information from LinkedIn post content.

    Takes raw HTML and text from a LinkedIn post and returns structured
    job information including title, company, skills, etc.
    """
    start_time = time.time()

    try:
        logger.info(f"Processing extraction request for {len(request.raw_html)} chars of HTML")

        # Extract job information
        extracted_info = await service.extract_job_info(
            request.raw_html,
            request.raw_text
        )

        processing_time = time.time() - start_time

        return ExtractionResponse(
            success=True,
            data=extracted_info,
            processing_time=round(processing_time, 2)
        )

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Extraction failed: {e}")

        return ExtractionResponse(
            success=False,
            error=str(e),
            processing_time=round(processing_time, 2)
        )


@router.get("/health", response_model=HealthResponse)
async def health_check(
    service: ExtractionService = Depends(get_extraction_service)
) -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        models_loaded=["spaCy", "OpenAI"],
        uptime=time.time()  # Simplified uptime
    )


@router.post("/extract/batch")
async def extract_batch(
    requests: list[ExtractionRequest],
    service: ExtractionService = Depends(get_extraction_service)
) -> Dict[str, Any]:
    """
    Extract job information from multiple LinkedIn posts in batch.

    Useful for processing multiple posts efficiently.
    """
    if len(requests) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 posts per batch request"
        )

    start_time = time.time()
    results = []

    try:
        for i, request in enumerate(requests):
            try:
                logger.info(f"Processing batch item {i+1}/{len(requests)}")

                extracted_info = await service.extract_job_info(
                    request.raw_html,
                    request.raw_text
                )

                results.append({
                    "index": i,
                    "success": True,
                    "data": extracted_info.dict(),
                })

            except Exception as e:
                logger.error(f"Batch item {i+1} failed: {e}")
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e),
                })

        processing_time = time.time() - start_time

        return {
            "total_processed": len(results),
            "successful": len([r for r in results if r["success"]]),
            "failed": len([r for r in results if not r["success"]]),
            "results": results,
            "total_processing_time": round(processing_time, 2),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


