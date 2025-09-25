import uuid
import json
import yaml
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

# Import repositories and utilities
from app.repositories.scylla_repo import get_scylla_repository
from app.repositories.vector_repo import get_singleton_vector_repository
from app.utils.embeddings import generate_job_embedding
from app.models.job_models import JobVector

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def insert_single_job(job_data: Dict) -> bool:
    """Insert a single job into both ScyllaDB and Vector DB"""
    try:
        job_id = job_data["job_id"]
        logger.info(f"Inserting job {job_id}: {job_data['title']}")
        
        # 1. Insert into ScyllaDB
        scylla_repo = get_scylla_repository()
        scylla_success = scylla_repo.insert_job(job_data)
        
        if not scylla_success:
            logger.error(f"Failed to insert job {job_id} into ScyllaDB")
            return False
        
        # 2. Generate embedding and insert into Vector DB
        embedding = generate_job_embedding(
            title=job_data["title"],
            description=job_data["description"],
            skills=job_data["skills"],
            category=job_data.get("category")
        )
        
        job_vector = JobVector(
            job_id=job_id,
            embedding=embedding,
            title_snippet=job_data["title"],
            category=job_data.get("category"),
            skills=job_data["skills"]
        )
        
        vector_repo = get_singleton_vector_repository()
        vector_success = vector_repo.insert_job_vector(job_vector)
        
        if not vector_success:
            logger.error(f"Failed to insert job {job_id} into Vector DB")
            return False
        
        logger.info(f"Successfully inserted job {job_id} into both databases ✅")
        return True
        
    except Exception as e:
        logger.error(f"Error inserting job: {str(e)}")
        return False

def insert_jobs_from_data(jobs_data: List[Dict]) -> int:
    """Insert multiple jobs from data list"""
    success_count = 0
    
    for job_data in jobs_data:
        # Ensure job_id is UUID type
        if not isinstance(job_data["job_id"], uuid.UUID):
            job_data["job_id"] = uuid.UUID(job_data["job_id"]) if isinstance(job_data["job_id"], str) else uuid.uuid4()
        
        # Ensure provider_id is UUID type
        if not isinstance(job_data["provider_id"], uuid.UUID):
            job_data["provider_id"] = uuid.UUID(job_data["provider_id"]) if isinstance(job_data["provider_id"], str) else uuid.uuid4()
        
        # Ensure timestamps are datetime objects
        if isinstance(job_data.get("date_posted"), str):
            job_data["date_posted"] = datetime.fromisoformat(job_data["date_posted"])
        if isinstance(job_data.get("expiry_date"), str):
            job_data["expiry_date"] = datetime.fromisoformat(job_data["expiry_date"])
        
        if insert_single_job(job_data):
            success_count += 1
    
    logger.info(f"Successfully inserted {success_count}/{len(jobs_data)} jobs")
    return success_count

def load_jobs_from_json(file_path: str) -> List[Dict]:
    """Load jobs from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both single job and array of jobs
        if isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return data
        else:
            logger.error("Invalid JSON format: expected dict or list")
            return []
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {str(e)}")
        return []

def load_jobs_from_yaml(file_path: str) -> List[Dict]:
    """Load jobs from YAML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Handle both single job and array of jobs
        if isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return data
        else:
            logger.error("Invalid YAML format: expected dict or list")
            return []
    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {str(e)}")
        return []

def create_sample_jobs() -> List[Dict]:
    """Create sample job data for testing"""
    base_time = datetime.utcnow()
    
    sample_jobs = [
        {
            "job_id": uuid.uuid4(),
            "provider_id": uuid.uuid4(),
            "title": "Senior Backend Engineer",
            "description": "We are looking for a senior backend engineer with expertise in Python and FastAPI. You will be responsible for designing and implementing scalable APIs, working with databases, and ensuring high performance systems. Experience with microservices architecture is a plus.",
            "category": "Software Engineering",
            "city": "Dhaka",
            "country": "Bangladesh",
            "latitude": 23.8103,
            "longitude": 90.4125,
            "employment_type": "full-time",
            "salary_min": 80000,
            "salary_max": 120000,
            "currency": "BDT",
            "experience_level": "senior",
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
            "status": "active",
            "is_verified": True,
            "date_posted": base_time,
            "expiry_date": base_time + timedelta(days=30),
        },
        {
            "job_id": uuid.uuid4(),
            "provider_id": uuid.uuid4(),
            "title": "AI/ML Engineer",
            "description": "Join our AI team to develop cutting-edge machine learning models. You will work on data preprocessing, model training, and deployment. Experience with TensorFlow, PyTorch, and cloud platforms is essential.",
            "category": "AI/ML",
            "city": "Dhaka",
            "country": "Bangladesh",
            "latitude": 23.8103,
            "longitude": 90.4125,
            "employment_type": "full-time",
            "salary_min": 90000,
            "salary_max": 150000,
            "currency": "BDT",
            "experience_level": "mid",
            "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Data Science"],
            "status": "active",
            "is_verified": True,
            "date_posted": base_time - timedelta(days=2),
            "expiry_date": base_time + timedelta(days=28),
        },
        {
            "job_id": uuid.uuid4(),
            "provider_id": uuid.uuid4(),
            "title": "Frontend Developer",
            "description": "We need a talented frontend developer to create beautiful and responsive user interfaces. You should be proficient in React, TypeScript, and modern CSS frameworks. Experience with state management libraries is required.",
            "category": "Software Engineering",
            "city": "Chittagong",
            "country": "Bangladesh",
            "latitude": 22.3569,
            "longitude": 91.7832,
            "employment_type": "full-time",
            "salary_min": 50000,
            "salary_max": 80000,
            "currency": "BDT",
            "experience_level": "mid",
            "skills": ["React", "TypeScript", "CSS", "JavaScript", "Redux"],
            "status": "active",
            "is_verified": True,
            "date_posted": base_time - timedelta(days=1),
            "expiry_date": base_time + timedelta(days=29),
        },
        {
            "job_id": uuid.uuid4(),
            "provider_id": uuid.uuid4(),
            "title": "Data Scientist",
            "description": "Looking for a data scientist to analyze large datasets and extract meaningful insights. You will work with business stakeholders to understand requirements and build predictive models. Strong statistical background required.",
            "category": "Data Science",
            "city": "Dhaka",
            "country": "Bangladesh",
            "latitude": 23.8103,
            "longitude": 90.4125,
            "employment_type": "contract",
            "salary_min": 70000,
            "salary_max": 100000,
            "currency": "BDT",
            "experience_level": "mid",
            "skills": ["Python", "Pandas", "Scikit-learn", "SQL", "Statistics"],
            "status": "active",
            "is_verified": True,
            "date_posted": base_time - timedelta(days=3),
            "expiry_date": base_time + timedelta(days=27),
        },
        {
            "job_id": uuid.uuid4(),
            "provider_id": uuid.uuid4(),
            "title": "DevOps Engineer",
            "description": "We are seeking a DevOps engineer to manage our cloud infrastructure and CI/CD pipelines. You will work with AWS, Docker, Kubernetes, and various automation tools. Strong Linux skills are essential.",
            "category": "DevOps",
            "city": "Sylhet",
            "country": "Bangladesh",
            "latitude": 24.8949,
            "longitude": 91.8687,
            "employment_type": "full-time",
            "salary_min": 75000,
            "salary_max": 110000,
            "currency": "BDT",
            "experience_level": "senior",
            "skills": ["AWS", "Docker", "Kubernetes", "Jenkins", "Linux"],
            "status": "active",
            "is_verified": True,
            "date_posted": base_time - timedelta(hours=12),
            "expiry_date": base_time + timedelta(days=30),
        }
    ]
    
    return sample_jobs

def main():
    """Main function to run the job insertion script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Insert jobs into ScyllaDB and Vector DB")
    parser.add_argument("--file", "-f", help="Path to JSON/YAML file containing job data")
    parser.add_argument("--format", choices=["json", "yaml"], default="json", help="File format (default: json)")
    parser.add_argument("--sample", action="store_true", help="Insert sample jobs for testing")
    
    args = parser.parse_args()
    
    if args.sample:
        # Insert sample jobs
        logger.info("Creating and inserting sample jobs...")
        sample_jobs = create_sample_jobs()
        success_count = insert_jobs_from_data(sample_jobs)
        logger.info(f"Sample job insertion completed: {success_count} jobs inserted")
        
    elif args.file:
        # Insert jobs from file
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"File not found: {args.file}")
            return
        
        logger.info(f"Loading jobs from {args.file} (format: {args.format})")
        
        if args.format == "json":
            jobs_data = load_jobs_from_json(args.file)
        else:
            jobs_data = load_jobs_from_yaml(args.file)
        
        if jobs_data:
            success_count = insert_jobs_from_data(jobs_data)
            logger.info(f"File job insertion completed: {success_count} jobs inserted")
        else:
            logger.error("No jobs found in file")
    
    else:
        # Insert single hardcoded job (legacy behavior)
        logger.info("Inserting single hardcoded job...")
        
        job = {
            "job_id": uuid.uuid4(),
            "provider_id": uuid.uuid4(),
            "title": "Backend Engineer",
            "description": "Work with Python and FastAPI to build scalable backend systems. You will be responsible for API development, database design, and system optimization.",
            "category": "Software Engineering",
            "city": "Dhaka",
            "country": "Bangladesh",
            "latitude": 23.8103,
            "longitude": 90.4125,
            "employment_type": "full-time",
            "salary_min": 40000,
            "salary_max": 60000,
            "currency": "BDT",
            "experience_level": "mid",
            "skills": ["Python", "FastAPI"],
            "status": "active",
            "is_verified": True,
            "date_posted": datetime.utcnow(),
            "expiry_date": datetime.utcnow() + timedelta(days=30),
        }

        if insert_single_job(job):
            logger.info("Single job insertion completed successfully")
        else:
            logger.error("Single job insertion failed")

if __name__ == "__main__":
    main()
