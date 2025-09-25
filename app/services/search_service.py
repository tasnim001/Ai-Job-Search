import logging
from typing import List, Dict, Set
from uuid import UUID
from app.utils import query_parser, embeddings
from app.repositories.scylla_repo import get_scylla_repository
from app.repositories.vector_repo import get_singleton_vector_repository
from app.models.job_models import Job, SearchResponse, ParsedFilters
from app.config import MAX_FINAL_RESULTS, MAX_VECTOR_RESULTS, MAX_SCYLLA_RESULTS

logger = logging.getLogger(__name__)

def search_jobs(query: str) -> SearchResponse:
    """
    Main search function implementing the business logic from PRD.
    
    Process Flow:
    1. Parse query into structured filters
    2. Get semantic matches from Vector DB (top-N job IDs)  
    3. Apply structured filters in Scylla
    4. Merge + rank results
    """
    logger.info(f"Searching for jobs with query: {query}")
    
    try:
        # 1. Parse query into structured filters
        parsed_filters = query_parser.parse_query(query)
        logger.info(f"Parsed filters: {parsed_filters}")

        # 2. Generate embedding for semantic search
        query_embedding = embeddings.get_query_embedding(query)
        logger.info(f"Generated embedding with dimension: {len(query_embedding)}")

        # 3. Get semantic matches from Vector DB
        vector_repo = get_singleton_vector_repository()
        vector_results = vector_repo.search_jobs(query_embedding, limit=MAX_VECTOR_RESULTS)
        logger.info(f"Vector search returned {len(vector_results)} results")

        # 4. Get structured matches from Scylla
        scylla_repo = get_scylla_repository()
        scylla_results = scylla_repo.filter_jobs(parsed_filters, limit=MAX_SCYLLA_RESULTS)
        logger.info(f"Scylla filter returned {len(scylla_results)} results")

        # 5. Merge results and avoid duplicates
        merged_jobs = _merge_and_rank_results(
            vector_results, 
            scylla_results, 
            parsed_filters
        )

        # 6. Limit final results
        final_results = merged_jobs[:MAX_FINAL_RESULTS]
        
        logger.info(f"Returning {len(final_results)} final results")
        
        return SearchResponse(
            query=query, 
            parsed_filters=parsed_filters, 
            results=final_results
        )
        
    except Exception as e:
        logger.error(f"Error in search_jobs: {str(e)}")
        # Return empty results on error
        return SearchResponse(
            query=query,
            parsed_filters=ParsedFilters(),
            results=[]
        )

def _merge_and_rank_results(
    vector_results: List[Dict], 
    scylla_results: List[Dict], 
    parsed_filters: ParsedFilters
) -> List[Job]:
    """
    Merge vector and Scylla results, removing duplicates and ranking by relevance.
    """
    
    # Step 1: Create a map for fast lookup of Scylla jobs
    scylla_job_map = {job["job_id"]: job for job in scylla_results}
    
    # Step 2: Process vector results and enrich with Scylla data
    processed_jobs = {}
    
    # Process vector search results first (they have semantic similarity scores)
    for vector_result in vector_results:
        job_id = vector_result["job_id"]
        
        # Try to get full job data from Scylla
        scylla_job = scylla_job_map.get(job_id)
        
        if scylla_job:
            # Merge vector result with complete Scylla data
            job = _create_job_from_data(scylla_job, vector_result["match_score"])
        else:
            # Use vector data only (might be incomplete)
            job = _create_job_from_vector_result(vector_result)
        
        if job and _passes_filters(job, parsed_filters):
            processed_jobs[job_id] = job
    
    # Step 3: Add Scylla-only results (not found in vector search)
    for scylla_job in scylla_results:
        job_id = scylla_job["job_id"]
        
        if job_id not in processed_jobs:
            # Calculate a base score for Scylla-only results
            base_score = _calculate_text_similarity_score(scylla_job, parsed_filters)
            job = _create_job_from_data(scylla_job, base_score)
            
            if job and _passes_filters(job, parsed_filters):
                processed_jobs[job_id] = job
    
    # Step 4: Sort by match score (highest first)
    sorted_jobs = sorted(
        processed_jobs.values(), 
        key=lambda job: job.match_score or 0, 
        reverse=True
    )
    
    return sorted_jobs

def _create_job_from_data(job_data: Dict, match_score: float) -> Job:
    """Create Job object from Scylla job data with match score."""
    try:
        return Job(
            job_id=job_data["job_id"],
            provider_id=job_data.get("provider_id"),
            title=job_data["title"],
            description=job_data.get("description"),
            category=job_data.get("category"),
            city=job_data.get("city"),
            country=job_data.get("country"),
            latitude=job_data.get("latitude"),
            longitude=job_data.get("longitude"),
            employment_type=job_data.get("employment_type"),
            salary_min=job_data.get("salary_min"),
            salary_max=job_data.get("salary_max"),
            currency=job_data.get("currency"),
            experience_level=job_data.get("experience_level"),
            skills=list(job_data.get("skills", [])) if job_data.get("skills") else [],
            status=job_data.get("status"),
            is_verified=job_data.get("is_verified"),
            date_posted=job_data.get("date_posted"),
            expiry_date=job_data.get("expiry_date"),
            match_score=match_score
        )
    except Exception as e:
        logger.error(f"Error creating job from data: {str(e)}")
        return None

def _create_job_from_vector_result(vector_result: Dict) -> Job:
    """Create Job object from vector search result (may have limited data)."""
    try:
        return Job(
            job_id=vector_result["job_id"],
            title=vector_result.get("title_snippet", ""),
            category=vector_result.get("category"),
            skills=vector_result.get("skills", []),
            match_score=vector_result.get("match_score", 0.0)
        )
    except Exception as e:
        logger.error(f"Error creating job from vector result: {str(e)}")
        return None

def _passes_filters(job: Job, filters: ParsedFilters) -> bool:
    """Check if job passes additional filter criteria."""
    
    # Check salary range
    if filters.salary_min and job.salary_min and job.salary_min < filters.salary_min:
        return False
    
    if filters.salary_max and job.salary_max and job.salary_max > filters.salary_max:
        return False
    
    # Check skills overlap (if specified)
    if filters.skills and job.skills:
        job_skills_set = set(skill.lower() for skill in job.skills)
        filter_skills_set = set(skill.lower() for skill in filters.skills)
        if not filter_skills_set.intersection(job_skills_set):
            return False
    
    # Check location (if specified and available)
    if filters.location and job.city:
        if filters.location.lower() != job.city.lower():
            return False
    
    # Check employment type
    if filters.employment_type and job.employment_type:
        if filters.employment_type.lower() != job.employment_type.lower():
            return False
    
    # Check experience level
    if filters.experience_level and job.experience_level:
        if filters.experience_level.lower() != job.experience_level.lower():
            return False
    
    # Check category
    if filters.category and job.category:
        if filters.category.lower() != job.category.lower():
            return False
    
    return True

def _calculate_text_similarity_score(job_data: Dict, filters: ParsedFilters) -> float:
    """
    Calculate a basic text similarity score for jobs that weren't found in vector search.
    This gives Scylla-only results a reasonable ranking.
    """
    score = 0.5  # Base score for Scylla matches
    
    # Boost score for keyword matches in title/description
    title = (job_data.get("title") or "").lower()
    description = (job_data.get("description") or "").lower()
    
    keyword_matches = 0
    for keyword in filters.keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in title:
            keyword_matches += 2  # Title matches are worth more
        elif keyword_lower in description:
            keyword_matches += 1
    
    # Add keyword bonus (up to 0.3 points)
    score += min(keyword_matches * 0.05, 0.3)
    
    # Boost for skills matches
    if filters.skills and job_data.get("skills"):
        job_skills = set(skill.lower() for skill in job_data["skills"])
        filter_skills = set(skill.lower() for skill in filters.skills)
        skill_overlap = len(job_skills.intersection(filter_skills))
        score += min(skill_overlap * 0.1, 0.2)
    
    return min(score, 1.0)  # Cap at 1.0
