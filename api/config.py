"""Configuration for MarginGuard API"""

import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "marginGuard")

# Embedding Model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# FastAPI
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

print(f"Config loaded: DB={DB_HOST}:{DB_PORT}/{DB_NAME}, Embedding={EMBEDDING_MODEL}")
