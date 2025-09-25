from pydantic import BaseModel
from typing import List, Optional, Set
from uuid import UUID
from datetime import datetime

class Job(BaseModel):
    job_id: UUID
    provider_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    employment_type: Optional[str] = None  # full-time, part-time, contract
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = None
    experience_level: Optional[str] = None
    skills: List[str] = []
    status: Optional[str] = None  # active, filled, draft
    is_verified: Optional[bool] = None
    date_posted: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    match_score: Optional[float] = None

class ParsedFilters(BaseModel):
    intent: Optional[str] = "job_search"
    keywords: List[str] = []
    location: Optional[str] = None
    geo_radius_km: Optional[int] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    skills: List[str] = []
    category: Optional[str] = None
    status: Optional[str] = "active"
    detected_language: Optional[str] = None
    original_query: Optional[str] = None

class JobVector(BaseModel):
    job_id: UUID
    embedding: List[float]
    title_snippet: str
    category: Optional[str] = None
    skills: List[str] = []

class SearchResponse(BaseModel):
    query: str
    parsed_filters: ParsedFilters
    results: List[Job]

class JobInsert(BaseModel):
    """Model for inserting new jobs"""
    provider_id: UUID
    title: str
    description: str
    category: str
    city: str
    country: str
    latitude: float
    longitude: float
    employment_type: str
    salary_min: int
    salary_max: int
    currency: str
    experience_level: str
    skills: List[str]
    status: str = "active"
    is_verified: bool = True
