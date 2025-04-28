from bs4 import BeautifulSoup
import re
import logging
from app.models.schemas import FacebookPageData
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class FacebookParser:
    """
    Parser for extracting structured data from Facebook pages.
    """
    
    def parse_page(self, soup: BeautifulSoup, url: str) -> FacebookPageData:
        """
        Extract structured data from a Facebook page.
        
        Args:
            soup: BeautifulSoup object containing the parsed HTML
            url: The URL of the Facebook page
            
        Returns:
            FacebookPageData: Structured data extracted from the page
        """
        data = FacebookPageData(
            page_url=url,
            scraped_date=datetime.now().isoformat()
        )
        
        try:
            # Extract page name
            self._extract_page_name(soup, data)
            
            # Extract email addresses
            self._extract_email(soup, data)
            
            # Extract phone numbers
            self._extract_phone(soup, data)
            
            # Extract website
            self._extract_website(soup, data)
            
            # Extract address
            self._extract_address(soup, data)
            
            return data
            
        except Exception as e:
            logger.error(f"Error parsing Facebook page: {e}")
            return data
    
    def _extract_page_name(self, soup: BeautifulSoup, data: FacebookPageData) -> None:
        """Extract the page name."""
        try:
            # Try to find the page name in the title
            title_element = soup.select_one('title')
            if title_element:
                title = title_element.text.strip()
                # Remove " - Facebook" suffix if present
                data.page_name = re.sub(r'\s*-\s*Facebook\s*$', '', title)
            
            # Try to find the page name in h1 elements
            if not data.page_name:
                h1_element = soup.select_one('h1')
                if h1_element:
                    data.page_name = h1_element.text.strip()
        except Exception as e:
            logger.error(f"Error extracting page name: {e}")
    
    def _extract_email(self, soup: BeautifulSoup, data: FacebookPageData) -> None:
        """Extract email addresses from the page."""
        try:
            # Method 1: Look for mailto links
            email_links = soup.select('a[href^="mailto:"]')
            for link in email_links:
                href = link.get('href', '')
                if href.startswith('mailto:'):
                    email = href.replace('mailto:', '').strip()
                    if self._is_valid_email(email):
                        data.email = email
                        return
            
            # Method 2: Look for email patterns in the text
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            body_text = ' '.join(soup.select('body')[0].stripped_strings) if soup.select('body') else ''
            email_matches = re.findall(email_pattern, body_text)
            
            for email in email_matches:
                if self._is_valid_email(email):
                    data.email = email
                    return
        except Exception as e:
            logger.error(f"Error extracting email: {e}")
    
    def _extract_phone(self, soup: BeautifulSoup, data: FacebookPageData) -> None:
        """Extract phone numbers from the page."""
        try:
            # Look for tel: links
            phone_links = soup.select('a[href^="tel:"]')
            for link in phone_links:
                href = link.get('href', '')
                if href.startswith('tel:'):
                    phone = href.replace('tel:', '').strip()
                    data.phone = phone
                    return
            
            # Look for phone patterns in the text
            phone_pattern = r'(\+\d{1,3})?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
            body_text = ' '.join(soup.select('body')[0].stripped_strings) if soup.select('body') else ''
            phone_matches = re.findall(phone_pattern, body_text)
            
            if phone_matches:
                data.phone = phone_matches[0]
        except Exception as e:
            logger.error(f"Error extracting phone: {e}")
    
    def _extract_website(self, soup: BeautifulSoup, data: FacebookPageData) -> None:
        """Extract website links from the page."""
        try:
            # Look for external links
            for link in soup.select('a[href^="http"]'):
                href = link.get('href', '')
                if href and 'facebook.com' not in href and not href.startswith('/'):
                    data.website = href
                    return
        except Exception as e:
            logger.error(f"Error extracting website: {e}")
    
    def _extract_address(self, soup: BeautifulSoup, data: FacebookPageData) -> None:
        """Extract address information from the page."""
        try:
            # Look for address in sections that might contain it
            address_sections = soup.select('div:contains("Address"), div:contains("Location")')
            for section in address_sections:
                address_text = ' '.join(section.stripped_strings)
                if len(address_text) > 10:  # Simple heuristic to filter out too short texts
                    data.address = address_text
                    return
        except Exception as e:
            logger.error(f"Error extracting address: {e}")
    
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate if a string is a properly formatted email address."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _extract_number(self, text: str) -> Optional[int]:
        """Extract a number from text."""
        number_str = ''.join(c for c in text if c.isdigit())
        return int(number_str) if number_str else None