# 📘 Matchmaker Service API Documentation

## Overview

The **Matchmaker Service** is a job search platform backend that provides natural language job search capabilities using semantic search and structured filtering. It combines ScyllaDB for structured data storage with Weaviate for vector-based semantic search, powered by Google Gemini embeddings.

## Base URL
```
http://localhost:8000
```

## Authentication
No authentication required for this version.

---

## 🔍 Endpoints

### 1. Health Check

**GET** `/`

Returns the service status.

#### Response
```json
{
  "message": "Matchmaker Service is running!"
}
```

---

### 2. Search Jobs

**GET** `/search`

Search for jobs using natural language queries.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Natural language job search query |

#### Example Requests

```bash
# Basic search
GET /search?q=Python engineer in Dhaka

# Complex search with salary and skills
GET /search?q=Senior AI engineer with TensorFlow experience, minimum 80k salary in Dhaka

# Location and employment type
GET /search?q=Remote part-time frontend developer with React

# Experience level search
GET /search?q=Junior data scientist with Python experience

# Geo-radius search
GET /search?q=Jobs within 5km of Dhaka with 50k-70k salary
```

#### Response Format

```json
{
  "query": "Python engineer in Dhaka",
  "parsed_filters": {
    "intent": "job_search",
    "keywords": ["python", "engineer"],
    "location": "Dhaka",
    "geo_radius_km": null,
    "salary_min": null,
    "salary_max": null,
    "employment_type": null,
    "experience_level": null,
    "skills": ["Python"],
    "category": "Software Engineering",
    "status": "active"
  },
  "results": [
    {
      "job_id": "123e4567-e89b-12d3-a456-426614174000",
      "provider_id": "987fcdeb-51e2-4a3b-8b9c-123456789def",
      "title": "Senior Backend Engineer",
      "description": "We are looking for a senior backend engineer...",
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
      "is_verified": true,
      "date_posted": "2024-01-15T10:30:00Z",
      "expiry_date": "2024-02-15T10:30:00Z",
      "match_score": 0.95
    }
  ]
}
```

---

## 🧠 Query Understanding

The service intelligently parses natural language queries into structured filters:

### Supported Query Patterns

#### 1. **Location Detection**
- `"jobs in Dhaka"`
- `"software engineer in London"`
- `"remote work from Chittagong"`

**Supported Cities:**
- Bangladesh: Dhaka, Chittagong, Sylhet, Rajshahi, Khulna, Barisal, Rangpur, Mymensingh
- International: New York, London, Toronto, Sydney, Dubai, Singapore, Bangalore, Mumbai

#### 2. **Salary Ranges**
- `"40k-60k salary"`
- `"minimum 50k"`
- `"salary 40000 to 60000"`
- `"50k minimum salary"`

#### 3. **Employment Types**
- `"full-time"`
- `"part-time"`
- `"contract"`
- `"remote"`
- `"work from home"`

#### 4. **Experience Levels**
- `"junior developer"`
- `"senior engineer"`
- `"entry level"`
- `"mid-level"`
- `"experienced"`

#### 5. **Skills & Technologies**
```
Programming: Python, Java, JavaScript, TypeScript, C++, C#, Go, Rust, PHP, Ruby
Frameworks: React, Angular, Vue, FastAPI, Django, Flask, Spring
AI/ML: TensorFlow, PyTorch, Scikit-learn, Machine Learning, AI
Cloud: AWS, Azure, GCP, Docker, Kubernetes
Databases: MongoDB, PostgreSQL, MySQL, Redis
```

#### 6. **Job Categories**
- Software Engineering
- Data Science  
- AI/ML
- DevOps
- Design
- Marketing
- Sales
- Finance
- HR
- Education

#### 7. **Geo-Radius Search**
- `"within 2km"`
- `"5 kilometer radius"`
- `"jobs near me within 10km"`

---

## 📊 Response Fields

### Job Object

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | UUID | Unique job identifier |
| `provider_id` | UUID | Job provider identifier |
| `title` | string | Job title |
| `description` | string | Job description |
| `category` | string | Job category |
| `city` | string | Job location city |
| `country` | string | Job location country |
| `latitude` | number | Geographic latitude |
| `longitude` | number | Geographic longitude |
| `employment_type` | string | Employment type (full-time, part-time, contract) |
| `salary_min` | number | Minimum salary |
| `salary_max` | number | Maximum salary |
| `currency` | string | Salary currency |
| `experience_level` | string | Required experience level |
| `skills` | array[string] | Required skills |
| `status` | string | Job status (active, filled, draft) |
| `is_verified` | boolean | Whether job is verified |
| `date_posted` | datetime | Job posting date |
| `expiry_date` | datetime | Job expiry date |
| `match_score` | number | Relevance score (0.0-1.0) |

### Parsed Filters Object

| Field | Type | Description |
|-------|------|-------------|
| `intent` | string | Always "job_search" |
| `keywords` | array[string] | Extracted keywords |
| `location` | string | Detected location |
| `geo_radius_km` | number | Geographic search radius |
| `salary_min` | number | Minimum salary filter |
| `salary_max` | number | Maximum salary filter |
| `employment_type` | string | Employment type filter |
| `experience_level` | string | Experience level filter |
| `skills` | array[string] | Detected skills |
| `category` | string | Job category filter |
| `status` | string | Job status filter |

---

## 🔍 Example Queries & Responses

### Query 1: Basic Search
```bash
GET /search?q=Python developer
```

**Response:**
```json
{
  "query": "Python developer",
  "parsed_filters": {
    "intent": "job_search",
    "keywords": ["developer"],
    "skills": ["Python"],
    "category": "Software Engineering",
    "status": "active"
  },
  "results": [
    {
      "job_id": "...",
      "title": "Senior Backend Engineer",
      "skills": ["Python", "FastAPI"],
      "match_score": 0.92
    }
  ]
}
```

### Query 2: Complex Search
```bash
GET /search?q=Senior AI engineer with TensorFlow experience, minimum 80k salary in Dhaka
```

**Response:**
```json
{
  "query": "Senior AI engineer with TensorFlow experience, minimum 80k salary in Dhaka",
  "parsed_filters": {
    "intent": "job_search",
    "keywords": ["engineer"],
    "location": "Dhaka",
    "salary_min": 80000,
    "experience_level": "senior",
    "skills": ["TensorFlow"],
    "category": "AI/ML",
    "status": "active"
  },
  "results": [
    {
      "job_id": "...",
      "title": "AI/ML Engineer", 
      "city": "Dhaka",
      "salary_min": 90000,
      "experience_level": "mid",
      "skills": ["Python", "TensorFlow", "PyTorch"],
      "match_score": 0.89
    }
  ]
}
```

### Query 3: Remote Work
```bash
GET /search?q=Remote React developer part-time
```

**Response:**
```json
{
  "query": "Remote React developer part-time",
  "parsed_filters": {
    "intent": "job_search",
    "keywords": ["developer"],
    "employment_type": "remote",
    "skills": ["React"],
    "category": "Software Engineering",
    "status": "active"
  },
  "results": [...]
}
```

---

## 🚫 Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid query parameters |
| 422 | Unprocessable Entity - Invalid input format |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["query", "q"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

---

## ⚡ Performance & Limits

| Metric | Value |
|--------|-------|
| Max Results | 20 jobs per request |
| Vector Search Limit | 50 results |
| Scylla Search Limit | 100 results |
| Query Timeout | 30 seconds |
| Rate Limit | None (currently) |

---

## 🔧 Technical Details

### Search Algorithm
1. **Query Parsing**: Natural language → structured filters
2. **Embedding Generation**: Google Gemini text-embedding-004 
3. **Vector Search**: Weaviate semantic similarity search
4. **Structured Filtering**: ScyllaDB SQL-like filtering
5. **Result Merging**: Deduplication and relevance ranking
6. **Score Calculation**: Weighted combination of semantic + filter matches

### Database Architecture
- **ScyllaDB**: Structured job data with secondary indexes
- **Weaviate**: Vector embeddings for semantic search
- **Embedding Model**: Google Gemini text-embedding-004 (768 dimensions)

---

## 🚀 Interactive Documentation

Visit `http://localhost:8000/docs` for interactive API documentation with:
- Live API testing
- Request/response examples  
- Parameter validation
- Schema exploration

---

## 📝 Sample Test Data

The service includes 5 sample jobs:

1. **Senior Backend Engineer** (Dhaka) - Python, FastAPI, PostgreSQL
2. **AI/ML Engineer** (Dhaka) - Python, TensorFlow, PyTorch
3. **Frontend Developer** (Chittagong) - React, TypeScript, CSS
4. **Data Scientist** (Dhaka) - Python, Pandas, Scikit-learn
5. **DevOps Engineer** (Sylhet) - AWS, Docker, Kubernetes

---

## 🎯 Usage Tips

1. **Be Specific**: More detailed queries yield better results
2. **Use Natural Language**: The system understands conversational queries
3. **Combine Filters**: Mix location, salary, skills for precise results
4. **Check Match Scores**: Higher scores indicate better matches
5. **Experiment**: Try different phrasings for the same requirement

---

**API Version**: 1.0  
**Last Updated**: January 2024  
**Service**: Matchmaker Job Search Platform
