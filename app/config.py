import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
SCYLLA_HOSTS = os.getenv("SCYLLA_HOSTS", "127.0.0.1").split(",")
SCYLLA_PORT = int(os.getenv("SCYLLA_PORT", "9042"))
SCYLLA_KEYSPACE = os.getenv("SCYLLA_KEYSPACE", "jobs_keyspace")

# Vector DB Configuration (Weaviate Only)
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", None)

# Google Gemini Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDyYcmgp1v5WEVzh79jGotFYw1CK1rBTrU")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Search Configuration
MAX_VECTOR_RESULTS = int(os.getenv("MAX_VECTOR_RESULTS", "50"))
MAX_SCYLLA_RESULTS = int(os.getenv("MAX_SCYLLA_RESULTS", "100"))
MAX_FINAL_RESULTS = int(os.getenv("MAX_FINAL_RESULTS", "20"))
