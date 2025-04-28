import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock
from app.models.schemas import FacebookPageData

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@patch("app.services.scraper.FacebookScraper")
def test_scrape_endpoint_success(mock_scraper):
    """Test the scrape endpoint with a successful response."""
    # Mock the scraper's scrape_page method
    mock_instance = MagicMock()
    mock_scraper.return_value = mock_instance
    
    # Create a mock FacebookPageData object
    mock_data = FacebookPageData(
        page_name="Test Page",
        page_url="https://www.facebook.com/testpage/about",
        email="test@example.com",
        website="https://www.example.com",
        scraped_date="2025-04-28T14:30:00.000000"
    )
    
    # Set the return value for the scrape_page method
    mock_instance.scrape_page.return_value = mock_data
    
    # Make the request
    response = client.post(
        "/api/scrape",
        json={"url": "https://www.facebook.com/testpage"}
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["page_name"] == "Test Page"
    assert data["data"]["email"] == "test@example.com"
    assert data["error"] is None


@patch("app.services.scraper.FacebookScraper")
def test_scrape_endpoint_failure(mock_scraper):
    """Test the scrape endpoint with an error response."""
    # Mock the scraper's scrape_page method to raise an exception
    mock_instance = MagicMock()
    mock_scraper.return_value = mock_instance
    mock_instance.scrape_page.side_effect = Exception("Failed to scrape page")
    
    # Make the request
    response = client.post(
        "/api/scrape",
        json={"url": "https://www.facebook.com/testpage"}
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["data"] is None
    assert data["error"] == "Failed to scrape page"


def test_scrape_endpoint_invalid_url():
    """Test the scrape endpoint with an invalid URL."""
    # Make the request with an invalid URL
    response = client.post(
        "/api/scrape",
        json={"url": "not-a-valid-url"}
    )
    
    # Check the response
    assert response.status_code == 422  # Validation error