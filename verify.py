
import asyncio
from dotenv import load_dotenv
from app.services.gemini_service import GeminiService

load_dotenv()

async def main():
    print("Testing Gemini Service with gemini-flash-latest...")
    service = GeminiService()
    await service.initialize()
    
    # Mock data
    text = "We are hiring a Senior React Developer at TechCorp. Location: San Francisco. Skills: React, TypeScript, Node.js. Salary: $150k - $180k."
    print(f"Input Text: {text}")
    print("Extracting...")
    
    result = await service.extract_job_info(text, {})
    
    print("\nExtraction Result:")
    import json
    print(json.dumps(result, indent=2))
    
    await service.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
