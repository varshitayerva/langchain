import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Tavily Search API
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable not set. Add it to .env file.")

# Frankfurter API (free currency conversion - no key needed)
FRANKFURTER_BASE_URL = "https://api.frankfurter.dev/v2/rates"

# Research settings
MAX_COMPETITORS_TO_RETURN = 3
SEARCH_TIMEOUT = 5  # seconds
CURRENCY_CONVERSION_TIMEOUT = 5  # seconds
