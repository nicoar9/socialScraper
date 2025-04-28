import requests
import re
import json
import logging
import random
from datetime import datetime
from bs4 import BeautifulSoup
from app.models.schemas import FacebookPageData
from app.utils.helpers import extract_emails_from_text, is_valid_facebook_url, clean_text, is_valid_email
from app.utils.parser import FacebookParser

logger = logging.getLogger(__name__)

# User agents copied from existing spider
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
]


class FacebookScraper:
    """
    Service for scraping Facebook pages to extract email addresses and basic information.
    This class adapts the existing Scrapy spider's functionality to work with FastAPI.
    """
    
    def __init__(self):
        """Initialize the Facebook scraper with a session and parser."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
        self.parser = FacebookParser()
        
    async def scrape_page(self, url: str) -> FacebookPageData:
        """
        Scrape a Facebook page and extract email and basic information.
        
        Args:
            url: The URL of the Facebook page to scrape
            
        Returns:
            FacebookPageData: The extracted data from the Facebook page
            
        Raises:
            Exception: If there's an error during scraping
        """
        try:
            # Validate the URL
            if not is_valid_facebook_url(url):
                logger.warning(f"URL may not be a valid Facebook URL: {url}")
            
            # Ensure we're looking at the About page
            if 'about' not in url.lower():
                url = url.rstrip('/') + '/about'
                logger.info(f"Navigating directly to About page: {url}")
            
            # Make the request
            logger.info(f"Making request to: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse the content
            soup = BeautifulSoup(response.content, 'lxml')
            html_content = response.text
            
            # Extract data using the parser
            data = self.parser.parse_page(soup, url)
            
            # If the parser didn't find an email, try direct extraction methods
            if not data.email:
                emails = self._extract_emails_directly(soup, html_content)
                if emails:
                    data.email = emails[0]
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            raise Exception(f"Failed to fetch the page: {e}")
            
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            raise Exception(f"Error during page scraping: {e}")
    
    def _extract_emails_directly(self, soup: BeautifulSoup, html_content: str) -> list:
        """
        Extract emails directly from the HTML content using multiple methods.
        This is a fallback if the parser doesn't find an email.
        
        Args:
            soup: BeautifulSoup object containing the parsed HTML
            html_content: Raw HTML content as string
            
        Returns:
            list: List of extracted email addresses
        """
        emails = []
        
        # Method 1: Direct regex search in HTML (including unicode encoding)
        email_pattern = r'([a-zA-Z0-9_.+-]+)\\u0040([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)|([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
        email_matches = re.findall(email_pattern, html_content)
        
        for match in email_matches:
            if match[0] and match[1]:  # Unicode format: user\u0040domain.com
                email = f"{match[0]}@{match[1]}"
                emails.append(email)
                logger.info(f"Found email using direct regex (unicode): {email}")
            elif match[2]:  # Regular format: user@domain.com
                email = match[2]
                emails.append(email)
                logger.info(f"Found email using direct regex: {email}")
        
        # Method 2: Extract from JSON data in script tags
        script_tags = soup.select('script[type="application/json"]')
        for script in script_tags:
            script_content = script.text
            if script_content and ('profile_email' in script_content):
                try:
                    # Email exists in profile_email field
                    email_match = re.search(r'"field_type":"profile_email"[^}]+?"title":\{[^}]*"text":"([^"]+)"', script_content)
                    if email_match:
                        email = email_match.group(1).replace('\\u0040', '@')
                        emails.append(email)
                        logger.info(f"Found email using regex in JSON: {email}")
                        
                    # Try to parse the JSON if regex didn't work
                    if not emails:
                        try:
                            # Parse the JSON
                            json_content = script_content.strip()
                            data = json.loads(json_content)
                            
                            # Look for profile fields in the JSON structure
                            if 'require' in data:
                                for item_list in data['require']:
                                    if len(item_list) > 3 and isinstance(item_list[3], list) and len(item_list[3]) > 0:
                                        for obj in item_list[3]:
                                            if isinstance(obj, dict) and '__bbox' in obj:
                                                bbox = obj['__bbox']
                                                if 'result' in bbox and 'data' in bbox['result'] and 'user' in bbox['result']['data']:
                                                    user_data = bbox['result']['data']['user']
                                                    if 'about_app_sections' in user_data and 'nodes' in user_data['about_app_sections']:
                                                        for section in user_data['about_app_sections']['nodes']:
                                                            if 'activeCollections' in section and 'nodes' in section['activeCollections']:
                                                                for collection in section['activeCollections']['nodes']:
                                                                    if 'style_renderer' in collection and 'profile_field_sections' in collection['style_renderer']:
                                                                        for field_section in collection['style_renderer']['profile_field_sections']:
                                                                            if 'profile_fields' in field_section and 'nodes' in field_section['profile_fields']:
                                                                                for field in field_section['profile_fields']['nodes']:
                                                                                    if 'field_type' in field and 'title' in field:
                                                                                        field_type = field['field_type']
                                                                                        field_value = field['title'].get('text', '')
                                                                                        
                                                                                        if field_type == 'profile_email' and field_value:
                                                                                            # Clean up email (remove \u0040 for @ symbol)
                                                                                            email = field_value.replace('\u0040', '@')
                                                                                            emails.append(email)
                                                                                            logger.info(f"Found email using JSON parsing: {email}")
                        except Exception as e:
                            logger.error(f"Error parsing JSON structure: {e}")
                except Exception as e:
                    logger.error(f"Error parsing JSON from script tag: {e}")
        
        # Method 3: Look for mailto links
        if not emails:
            email_links = soup.select('a[href^="mailto:"]')
            for link in email_links:
                href = link.get('href', '')
                if href.startswith('mailto:'):
                    email = href.replace('mailto:', '').strip()
                    if email:
                        emails.append(email)
                        logger.info(f"Found email using mailto link: {email}")
        
        # Method 4: Look for email text in specific sections
        if not emails:
            contact_sections = soup.select('div:contains("Contact Info"), div:contains("Email"), div:contains("Contact")')
            for section in contact_sections:
                section_text = ' '.join(text for text in section.stripped_strings)
                found_emails = extract_emails_from_text(section_text)
                if found_emails:
                    emails.extend(found_emails)
                    logger.info(f"Found emails in contact section: {found_emails}")
        
        # Method 5: Look for emails in the entire page as a fallback
        if not emails:
            body_text = ' '.join(text for text in soup.body.stripped_strings) if soup.body else ''
            found_emails = extract_emails_from_text(body_text)
            if found_emails:
                emails.extend(found_emails)
                logger.info(f"Found emails in page body: {found_emails}")
        
        # Remove duplicates and clean up
        emails = list(dict.fromkeys([email.lower() for email in emails]))
        
        return emails