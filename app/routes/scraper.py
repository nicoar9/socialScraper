from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import ScraperRequest, ScraperResponse
from app.services.scraper import FacebookScraper
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["scraper"])


@router.post("/scrape", response_model=ScraperResponse)
async def scrape_facebook_page(request: ScraperRequest):
    """
    Scrape a Facebook page and extract relevant information.
    
    Args:
        request: The request containing the Facebook page URL to scrape
        
    Returns:
        ScraperResponse: The response containing the scraped data or error
    """
    try:
        logger.info(f"Received request to scrape: {request.url}")
        
        scraper = FacebookScraper()
        data = await scraper.scrape_page(str(request.url))
        
        logger.info(f"Successfully scraped page: {request.url}")
        return ScraperResponse(success=True, data=data)
    
    except Exception as e:
        logger.error(f"Error scraping page {request.url}: {str(e)}")
        return ScraperResponse(success=False, error=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        dict: A simple status message
    """
    return {"status": "healthy"}