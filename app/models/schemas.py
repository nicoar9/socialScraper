from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any


class ScraperRequest(BaseModel):
    """Request model for Facebook page scraping."""
    url: HttpUrl = Field(..., description="Facebook page URL to scrape")


class FacebookPageData(BaseModel):
    """Model for Facebook page data, focused on email extraction."""
    page_name: Optional[str] = Field(None, description="Name of the Facebook page")
    page_url: Optional[str] = Field(None, description="URL of the Facebook page")
    email: Optional[str] = Field(None, description="Email address found on the page")
    phone: Optional[str] = Field(None, description="Phone number found on the page")
    website: Optional[str] = Field(None, description="Website link found on the page")
    address: Optional[str] = Field(None, description="Physical address found on the page")
    scraped_date: Optional[str] = Field(None, description="Date and time of scraping")


class ScraperResponse(BaseModel):
    """Response model for Facebook page scraping."""
    success: bool
    data: Optional[FacebookPageData] = None
    error: Optional[str] = None