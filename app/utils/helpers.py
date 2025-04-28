import re
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


def is_valid_email(email):
    """
    Validate if a string is a properly formatted email address.
    
    Args:
        email: The email string to validate
        
    Returns:
        bool: True if the email is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_facebook_url(url):
    """
    Check if the URL appears to be a valid Facebook URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        bool: True if the URL is a valid Facebook URL, False otherwise
    """
    if not url:
        return False
        
    parsed = urlparse(url)
    return parsed.netloc in ('www.facebook.com', 'facebook.com', 'm.facebook.com', 'web.facebook.com')


def clean_text(text):
    """
    Clean text by removing extra whitespace and normalizing it.
    
    Args:
        text: The text to clean
        
    Returns:
        str: The cleaned text
    """
    if not text:
        return ""
        
    # Replace multiple whitespace with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove leading and trailing whitespace
    text = text.strip()
    return text


def extract_emails_from_text(text):
    """
    Extract email addresses from text using regex.
    
    Args:
        text: The text to extract emails from
        
    Returns:
        list: A list of valid email addresses found in the text
    """
    if not text:
        return []
        
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    found_emails = re.findall(email_pattern, text)
    
    # Filter out invalid emails and remove duplicates
    valid_emails = []
    seen = set()
    
    for email in found_emails:
        email = email.lower()
        if email not in seen and is_valid_email(email):
            valid_emails.append(email)
            seen.add(email)
            
    return valid_emails