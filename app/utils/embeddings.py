import google.generativeai as genai
from typing import List
from app.config import GOOGLE_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIMENSION
import logging

logger = logging.getLogger(__name__)

def get_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using Google Gemini API.
    Returns a vector representation of the input text.
    """
    try:
        # Configure Google AI
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Handle placeholder API key - return mock embedding
        if GOOGLE_API_KEY == "placeholder-google-api-key":
            logger.warning("Using placeholder Google API key - returning mock embedding")
            return generate_mock_embedding(text)
        
        # Get embedding from Google Gemini
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document"
        )
        
        return result['embedding']
        
    except Exception as e:
        logger.error(f"Error generating embedding with Gemini: {str(e)}")
        # Fallback to mock embedding on error
        return generate_mock_embedding(text)

def generate_mock_embedding(text: str) -> List[float]:
    """
    Generate a deterministic mock embedding based on text content.
    This ensures consistent results during development/testing.
    """
    import hashlib
    import struct
    
    # Create a hash of the text to ensure deterministic results
    text_hash = hashlib.md5(text.encode()).digest()
    
    # Convert hash to floats
    embedding = []
    for i in range(0, min(len(text_hash), EMBEDDING_DIMENSION * 4), 4):
        # Convert 4 bytes to float
        if i + 4 <= len(text_hash):
            float_val = struct.unpack('f', text_hash[i:i+4])[0]
            # Normalize to [-1, 1] range
            normalized_val = max(-1.0, min(1.0, float_val / 1e8))
            embedding.append(normalized_val)
    
    # Pad or truncate to desired dimension
    while len(embedding) < EMBEDDING_DIMENSION:
        embedding.append(0.0)
    
    return embedding[:EMBEDDING_DIMENSION]

def generate_job_embedding(title: str, description: str, skills: List[str], category: str = None) -> List[float]:
    """
    Generate embedding for a job by combining title, description, skills, and category.
    """
    # Combine job information into a single text
    job_text_parts = [title, description]
    
    if skills:
        job_text_parts.append("Skills: " + ", ".join(skills))
    
    if category:
        job_text_parts.append("Category: " + category)
    
    job_text = " | ".join(filter(None, job_text_parts))
    
    return get_embedding(job_text)

def get_query_embedding(query: str) -> List[float]:
    """
    Generate embedding for a search query using Google Gemini.
    Uses task_type="retrieval_query" for better search performance.
    """
    try:
        # Configure Google AI
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Handle placeholder API key - return mock embedding
        if GOOGLE_API_KEY == "placeholder-google-api-key":
            logger.warning("Using placeholder Google API key for query - returning mock embedding")
            return generate_mock_embedding(query)
        
        # Get embedding from Google Gemini with query-specific task type
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=query,
            task_type="retrieval_query"  # Optimized for search queries
        )
        
        return result['embedding']
        
    except Exception as e:
        logger.error(f"Error generating query embedding with Gemini: {str(e)}")
        # Fallback to regular embedding or mock
        return get_embedding(query)
