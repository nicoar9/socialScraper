import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import requests
from app.services.scraper import FacebookScraper
from app.models.schemas import FacebookPageData


@pytest.fixture
def mock_response():
    """Create a mock response with sample HTML content."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = """
    <html>
        <head>
            <title>Test Page - About | Facebook</title>
        </head>
        <body>
            <h1>Test Page</h1>
            <div>
                <a href="mailto:test@example.com">Email us</a>
                <a href="tel:+1234567890">Call us</a>
                <a href="https://www.example.com">Visit our website</a>
            </div>
            <div>
                Contact Info: test@example.com
            </div>
        </body>
    </html>
    """
    mock_resp.text = mock_resp.content.decode() if isinstance(mock_resp.content, bytes) else mock_resp.content
    return mock_resp


@patch("requests.Session")
async def test_scrape_page_success(mock_session, mock_response):
    """Test successful page scraping."""
    # Setup mock session
    session_instance = MagicMock()
    mock_session.return_value = session_instance
    session_instance.get.return_value = mock_response
    
    # Create scraper and call scrape_page
    scraper = FacebookScraper()
    result = await scraper.scrape_page("https://www.facebook.com/testpage")
    
    # Verify the result
    assert isinstance(result, FacebookPageData)
    assert result.page_name == "Test Page"
    assert result.email == "test@example.com"
    assert result.website is not None
    
    # Verify the session was used correctly
    session_instance.get.assert_called_once()
    args, kwargs = session_instance.get.call_args
    assert args[0] == "https://www.facebook.com/testpage/about"


@patch("requests.Session")
async def test_scrape_page_request_error(mock_session):
    """Test handling of request errors."""
    # Setup mock session to raise an exception
    session_instance = MagicMock()
    mock_session.return_value = session_instance
    session_instance.get.side_effect = requests.RequestException("Connection error")
    
    # Create scraper and call scrape_page
    scraper = FacebookScraper()
    
    # Verify that the exception is raised
    with pytest.raises(Exception) as excinfo:
        await scraper.scrape_page("https://www.facebook.com/testpage")
    
    assert "Failed to fetch the page" in str(excinfo.value)


def test_extract_emails_directly():
    """Test the direct email extraction methods."""
    # Create a sample HTML with different email formats
    html = """
    <html>
        <body>
            <a href="mailto:test1@example.com">Email 1</a>
            <div>Contact: test2@example.com</div>
            <script type="application/json">
                {"field_type":"profile_email","title":{"text":"test3\\u0040example.com"}}
            </script>
        </body>
    </html>
    """
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Create scraper and call _extract_emails_directly
    scraper = FacebookScraper()
    emails = scraper._extract_emails_directly(soup, html)
    
    # Verify the extracted emails
    assert len(emails) >= 2  # At least the mailto and text emails should be found
    assert "test1@example.com" in emails
    assert "test2@example.com" in emails