import weaviate
import logging
from typing import List, Dict, Optional
from uuid import UUID
from app.config import WEAVIATE_URL, WEAVIATE_API_KEY, MAX_VECTOR_RESULTS
from app.models.job_models import JobVector

logger = logging.getLogger(__name__)

class BaseVectorRepository:
    """Base class for vector database repositories"""
    
    def insert_job_vector(self, job_vector: JobVector) -> bool:
        """Insert job vector into vector database"""
        raise NotImplementedError
    
    def search_jobs(self, query_embedding: List[float], limit: int = None) -> List[Dict]:
        """Search for similar jobs using vector similarity"""
        raise NotImplementedError
    
    def delete_job_vector(self, job_id: UUID) -> bool:
        """Delete job vector from vector database"""
        raise NotImplementedError

class WeaviateRepository(BaseVectorRepository):
    """Weaviate vector database repository"""
    
    def __init__(self):
        self.client = None
        self.class_name = "JobsVector"
        self._connect()
        self._create_schema()
    
    def _connect(self):
        """Connect to Weaviate"""
        try:
            auth_config = weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY) if WEAVIATE_API_KEY else None
            self.client = weaviate.Client(
                url=WEAVIATE_URL,
                auth_client_secret=auth_config
            )
            logger.info(f"Connected to Weaviate at {WEAVIATE_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {str(e)}")
            raise
    
    def _create_schema(self):
        """Create Weaviate schema for jobs collection"""
        try:
            # Check if class already exists
            if self.client.schema.exists(self.class_name):
                logger.info(f"Weaviate class {self.class_name} already exists")
                return
            
            schema = {
                "class": self.class_name,
                "description": "Job vectors for semantic search",
                "vectorizer": "none",  # We provide our own vectors
                "properties": [
                    {
                        "name": "jobId",
                        "dataType": ["string"],
                        "description": "Job ID from ScyllaDB"
                    },
                    {
                        "name": "titleSnippet",
                        "dataType": ["text"],
                        "description": "Job title snippet"
                    },
                    {
                        "name": "category",
                        "dataType": ["string"],
                        "description": "Job category"
                    },
                    {
                        "name": "skills",
                        "dataType": ["string[]"],
                        "description": "Job skills"
                    }
                ]
            }
            
            self.client.schema.create_class(schema)
            logger.info(f"Created Weaviate class {self.class_name}")
        except Exception as e:
            logger.error(f"Failed to create Weaviate schema: {str(e)}")
            raise
    
    def insert_job_vector(self, job_vector: JobVector) -> bool:
        """Insert job vector into Weaviate"""
        try:
            data_object = {
                "jobId": str(job_vector.job_id),
                "titleSnippet": job_vector.title_snippet,
                "category": job_vector.category,
                "skills": job_vector.skills
            }
            
            uuid = self.client.data_object.create(
                data_object=data_object,
                class_name=self.class_name,
                vector=job_vector.embedding
            )
            
            logger.info(f"Inserted job vector {job_vector.job_id} into Weaviate")
            return True
        except Exception as e:
            logger.error(f"Failed to insert job vector: {str(e)}")
            return False
    
    def search_jobs(self, query_embedding: List[float], limit: int = None) -> List[Dict]:
        """Search for similar jobs in Weaviate"""
        try:
            if limit is None:
                limit = MAX_VECTOR_RESULTS
            
            result = self.client.query\
                .get(self.class_name, ["jobId", "titleSnippet", "category", "skills"])\
                .with_near_vector({"vector": query_embedding})\
                .with_limit(limit)\
                .with_additional(["certainty"])\
                .do()
            
            jobs = []
            if "data" in result and "Get" in result["data"] and self.class_name in result["data"]["Get"]:
                for item in result["data"]["Get"][self.class_name]:
                    jobs.append({
                        "job_id": UUID(item["jobId"]),
                        "title_snippet": item["titleSnippet"],
                        "category": item.get("category"),
                        "skills": item.get("skills", []),
                        "match_score": item["_additional"]["certainty"]
                    })
            
            logger.info(f"Found {len(jobs)} similar jobs in Weaviate")
            return jobs
        except Exception as e:
            logger.error(f"Failed to search jobs in Weaviate: {str(e)}")
            return []
    
    def delete_job_vector(self, job_id: UUID) -> bool:
        """Delete job vector from Weaviate"""
        try:
            # Find the object by jobId
            result = self.client.query\
                .get(self.class_name, ["jobId"])\
                .with_where({
                    "path": ["jobId"],
                    "operator": "Equal",
                    "valueString": str(job_id)
                })\
                .with_additional(["id"])\
                .do()
            
            if "data" in result and "Get" in result["data"] and self.class_name in result["data"]["Get"]:
                for item in result["data"]["Get"][self.class_name]:
                    object_id = item["_additional"]["id"]
                    self.client.data_object.delete(object_id)
                    logger.info(f"Deleted job vector {job_id} from Weaviate")
                    return True
            
            logger.warning(f"Job vector {job_id} not found in Weaviate")
            return False
        except Exception as e:
            logger.error(f"Failed to delete job vector: {str(e)}")
            return False


class MockVectorRepository(BaseVectorRepository):
    """Mock vector repository for development/testing"""
    
    def __init__(self):
        self.vectors = {}  # In-memory storage for development
        logger.info("Using mock vector repository")
    
    def insert_job_vector(self, job_vector: JobVector) -> bool:
        """Insert job vector into mock storage"""
        self.vectors[str(job_vector.job_id)] = {
            "embedding": job_vector.embedding,
            "title_snippet": job_vector.title_snippet,
            "category": job_vector.category,
            "skills": job_vector.skills
        }
        logger.info(f"Inserted job vector {job_vector.job_id} into mock storage")
        return True
    
    def search_jobs(self, query_embedding: List[float], limit: int = None) -> List[Dict]:
        """Search for similar jobs using mock similarity"""
        import random
        
        if limit is None:
            limit = MAX_VECTOR_RESULTS
        
        # Return mock results with random scores
        mock_jobs = [
            {
                "job_id": UUID("12345678-1234-5678-9abc-123456789abc"),
                "title_snippet": "AI Engineer",
                "category": "Software Engineering",
                "skills": ["Python", "TensorFlow", "Machine Learning"],
            "match_score": 0.95
        },
        {
                "job_id": UUID("87654321-4321-8765-cba9-987654321cba"),
                "title_snippet": "Backend Engineer",
                "category": "Software Engineering", 
                "skills": ["Python", "FastAPI", "PostgreSQL"],
            "match_score": 0.88
            },
            {
                "job_id": UUID("11111111-2222-3333-4444-555555555555"),
                "title_snippet": "Data Scientist",
                "category": "Data Science",
                "skills": ["Python", "Pandas", "Scikit-learn"],
                "match_score": 0.82
            }
        ]
        
        # Randomize scores slightly
        for job in mock_jobs:
            job["match_score"] += random.uniform(-0.1, 0.1)
            job["match_score"] = max(0.0, min(1.0, job["match_score"]))
        
        # Sort by score and limit
        mock_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        return mock_jobs[:limit]
    
    def delete_job_vector(self, job_id: UUID) -> bool:
        """Delete job vector from mock storage"""
        if str(job_id) in self.vectors:
            del self.vectors[str(job_id)]
            logger.info(f"Deleted job vector {job_id} from mock storage")
            return True
        return False

# Factory function to get Weaviate repository
def get_vector_repository() -> BaseVectorRepository:
    """Get Weaviate vector repository with fallback to mock"""
    try:
        return WeaviateRepository()
    except Exception as e:
        logger.error(f"Failed to initialize Weaviate repository: {str(e)}")
        logger.info("Falling back to mock repository")
        return MockVectorRepository()

# Singleton instance
_vector_repo = None

def get_singleton_vector_repository() -> BaseVectorRepository:
    """Get singleton vector repository instance"""
    global _vector_repo
    if _vector_repo is None:
        _vector_repo = get_vector_repository()
    return _vector_repo

# Legacy function for backward compatibility
def search_jobs(query_embedding: List[float]) -> List[Dict]:
    """Legacy function - use get_singleton_vector_repository().search_jobs() instead"""
    return get_singleton_vector_repository().search_jobs(query_embedding)