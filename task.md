# 📘 PRD: `matchmakerservice` (Job Search Platform Backend)

## 1. Objective

Develop a backend service (`matchmakerservice`) that allows users to perform **natural language job searches**.
The system must:

* Use **ScyllaDB** for structured data
* Use **Vector DB** (Weaviate or Pinecone) for semantic search
* Have a clean **layered FastAPI structure** (controller → service → repository)
* Handle job insertion via **offline script only** (no API migrations/inserts)

---

## 2. Tech Stack

* **Language:** Python 3.10
* **Framework:** FastAPI
* **DB 1 (Structured):** ScyllaDB
* **DB 2 (Vector):** Weaviate or Pinecone (final choice depends on deployment infra)
* **Embedding:** OpenAI `text-embedding-3-small` (or local alt like `sentence-transformers`)
* **Future Add-on:** Redis for geo-queries (radius-based search)

---

## 3. Architecture

### 3.1 Layered Design

* **Controller Layer (FastAPI routers)**

  * Receives HTTP requests, validates input, forwards to service layer
* **Service Layer**

  * Implements business logic (query parsing, merging Scylla + vector results)
* **Repository Layer**

  * Handles raw DB operations (Scylla + Vector DB connectors)
* **Utility Layer**

  * Embedding generator, query parser, helper methods

### 3.2 Project Structure

```
matchmakerservice/
 ├── app/
 │   ├── main.py                # FastAPI entrypoint
 │   ├── controllers/           # API endpoints (routers)
 │   │    └── search_controller.py
 │   ├── services/              # Business logic
 │   │    └── search_service.py
 │   ├── repositories/          # DB access logic
 │   │    ├── scylla_repo.py
 │   │    └── vector_repo.py
 │   ├── utils/                 # Helpers
 │   │    ├── embeddings.py
 │   │    └── query_parser.py
 │   ├── models/                # Pydantic models
 │   │    └── job_models.py
 │   └── config.py              # Config (DB URLs, API keys)
 ├── scripts/                   # Non-API scripts
 │   └── insert_jobs.py         # Manual job insertion
 ├── requirements.txt
 └── README.md
```

---

## 4. Data Model

### 4.1 ScyllaDB Table: `jobs`

* `job_id` (UUID, PK)
* `provider_id` (UUID)
* `title` (string)
* `description` (string)
* `category` (string)
* `city` (string)
* `country` (string)
* `latitude` (double)
* `longitude` (double)
* `employment_type` (string: full-time, part-time, contract)
* `salary_min` (int)
* `salary_max` (int)
* `currency` (string)
* `experience_level` (string)
* `skills` (set<string>)
* `status` (string: active, filled, draft)
* `is_verified` (boolean)
* `date_posted` (timestamp)
* `expiry_date` (timestamp)

### 4.2 Vector DB Collection: `jobs_vector`

* `job_id` (UUID, FK → Scylla)
* `embedding` (vector<float>)
* `title_snippet` (string)
* `category` (string, optional)
* `skills` (array<string>, optional)

---

## 5. Query Understanding

### 5.1 Input

User free-text queries, e.g.:

* “Jobs near me within 2km in Dhaka with 40k–60k salary”
* “Remote part-time Python tutor role for students”
* “AI engineer with TensorFlow experience, minimum 50k salary”

### 5.2 Output JSON Schema (always same structure)

```json
{
  "intent": "job_search",
  "keywords": ["Python", "Backend"],
  "location": "Dhaka",
  "geo_radius_km": 2,
  "salary_min": 40000,
  "salary_max": 60000,
  "employment_type": "full-time",
  "experience_level": "mid",
  "skills": ["Python", "FastAPI"],
  "category": "Software Engineering",
  "status": "active"
}
```

Notes:

* `geo_radius_km` must be included if mentioned (even though Redis isn’t hooked yet).
* If a field isn’t mentioned, return `null` or empty.
* `keywords` always captures extra free text for semantic search.

---

## 6. API Endpoints

### 6.1 `GET /search?q=<user_query>`

**Purpose:** Search for jobs.

**Process Flow:**

1. **Controller Layer** → Receives query string `q`.
2. **Service Layer** →

   * Parse query into JSON filters (via query parser).
   * Get semantic matches from Vector DB (top-N job IDs).
   * Apply structured filters in Scylla.
   * Merge + rank results.
3. **Return** → List of jobs with match scores + parsed filters.

**Response Example:**

```json
{
  "query": "Jobs near me within 2km in Dhaka with 40k–60k salary",
  "parsed_filters": {
    "location": "Dhaka",
    "geo_radius_km": 2,
    "salary_min": 40000,
    "salary_max": 60000
  },
  "results": [
    {
      "job_id": "uuid-1234",
      "title": "Backend Engineer",
      "city": "Dhaka",
      "salary_min": 40000,
      "salary_max": 60000,
      "skills": ["Python", "FastAPI"],
      "match_score": 0.92
    },
    {
      "job_id": "uuid-5678",
      "title": "ML Engineer",
      "city": "Dhaka",
      "salary_min": 45000,
      "salary_max": 55000,
      "skills": ["Python", "TensorFlow"],
      "match_score": 0.87
    }
  ]
}
```

---

## 7. Scripts

### 7.1 Job Insertion Script (`scripts/insert_jobs.py`)

* Reads job data from JSON/YAML or hardcoded dict.
* Inserts job metadata → **ScyllaDB**.
* Generates embedding (title + description + skills) → **Vector DB**.
* No API layer involved (direct DB + embeddings insert).

---

## 8. Non-Goals (MVP exclusions)

* No user authentication/authorization.
* No job application flow (only job search).
* No geo-radius query implementation (Redis integration is planned).
* No admin/moderator functionality.

---

## 9. Future Enhancements

* Add **Redis radius search** for `"near me"` queries.
* Support **multilingual queries**.
* Add **user profiles & recommendation engine**.
* Enable **job application workflows**.

