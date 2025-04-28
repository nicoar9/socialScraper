# Facebook Scraper API

A FastAPI-based service for extracting email addresses from Facebook pages.

## Features

- Simple API endpoint for scraping Facebook pages
- Extracts email addresses using multiple methods
- Also extracts basic page information (name, website, address)
- Handles anti-scraping measures with rotating user agents
- Proper error handling and logging

## Installation

### Prerequisites

- Python 3.9+
- pip

### Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd facebook-scraper-api
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running the API locally

Start the API server:

```
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

### API Endpoints

#### Scrape a Facebook page

```
POST /api/scrape
```

Request body:
```json
{
  "url": "https://www.facebook.com/example"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "page_name": "Example Page",
    "page_url": "https://www.facebook.com/example/about",
    "email": "contact@example.com",
    "phone": null,
    "website": "https://www.example.com",
    "address": null,
    "scraped_date": "2025-04-28T14:30:00.000000"
  },
  "error": null
}
```

### Using the API Documentation

FastAPI provides automatic API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Docker Deployment

1. Build the Docker image:
   ```
   docker build -t facebook-scraper-api .
   ```

2. Run the container:
   ```
   docker run -p 8000:8000 facebook-scraper-api
   ```

The API will be available at http://localhost:8000

## Important Notes

- Facebook's HTML structure changes frequently, so the email extraction logic may need regular updates
- Scraping may violate Facebook's Terms of Service - consider this for production use
- For high-volume scraping, you may need to implement more sophisticated anti-detection measures

## License

[MIT License](LICENSE)