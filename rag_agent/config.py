import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Postgres
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "fde_langchain")

# Groq LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set. Add it to .env file.")
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")

# Embedding model (free, no API key needed)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Tavily (free, no key for basic tier)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
