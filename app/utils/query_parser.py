import re
import json
import logging
from typing import List, Optional
import google.generativeai as genai
from app.models.job_models import ParsedFilters
from app.config import GOOGLE_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

def parse_query_with_gemini(query: str) -> ParsedFilters:
    """
    Parse natural language query using Gemini LLM for better understanding.
    Falls back to rule-based parsing if Gemini fails.
    """
    try:
        if GOOGLE_API_KEY == "placeholder-google-api-key":
            logger.warning("Using placeholder Google API key - falling back to rule-based parser")
            return parse_query_rule_based(query)
        
        # Configure Google AI
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Create the multilingual prompt for Gemini
        prompt = f"""
You are a multilingual job search query parser that understands queries in ANY language including English, Bengali/Bangla (বাংলা), Hindi, Arabic, Spanish, French, etc. Extract structured information from the natural language query and return ONLY a valid JSON object with these exact fields:

{{
  "intent": "job_search",
  "keywords": [],
  "location": null,
  "geo_radius_km": null,
  "salary_min": null,
  "salary_max": null,
  "employment_type": null,
  "experience_level": null,
  "skills": [],
  "category": null,
  "status": "active",
  "detected_language": null,
  "original_query": null
}}

MULTILINGUAL PARSING RULES:
- Understand queries in ANY language (English, বাংলা/Bengali, हिंदी/Hindi, العربية/Arabic, etc.)
- keywords: Extract main search terms in English (translate if needed)
- location: Extract city names in English format (ঢাকা → Dhaka, চট্টগ্রাম → Chittagong, etc.)
- geo_radius_km: Extract radius regardless of language ("২ কিমি এর মধ্যে" → 2)
- salary_min/salary_max: Extract salary ranges, handle different currency formats (৫০ হাজার → 50000)
- employment_type: "full-time", "part-time", "contract", or "remote" (in English)
- experience_level: "entry", "mid", or "senior" (in English)
- skills: Technical skills/technologies in English (পাইথন → Python, জাভাস্ক্রিপ্ট → JavaScript)
- category: Job category in English ("Software Engineering", "Data Science", "AI/ML", etc.)
- detected_language: Detect the primary language of the query (e.g., "bengali", "english", "hindi")
- original_query: Store the exact original query as provided
- Return null for missing fields, not empty strings

BENGALI/BANGLA SPECIFIC EXAMPLES:
- "ঢাকায় পাইথন ডেভেলপারের চাকরি" → location: "Dhaka", skills: ["Python"], category: "Software Engineering"
- "৫০ হাজার টাকা বেতনে সফটওয়্যার ইঞ্জিনিয়ার" → salary_min: 50000, category: "Software Engineering"
- "রিমোট ওয়ার্ক এআই ইঞ্জিনিয়ার" → employment_type: "remote", category: "AI/ML"
- "সিনিয়র ডেটা সায়েন্টিস্ট চট্টগ্রামে" → experience_level: "senior", location: "Chittagong", category: "Data Science"

COMMON TRANSLATIONS:
- চাকরি/কাজ → job
- ডেভেলপার → developer  
- ইঞ্জিনিয়ার → engineer
- ঢাকা → Dhaka, চট্টগ্রাম → Chittagong, সিলেট → Sylhet
- পাইথন → Python, জাভা → Java, রিয়েক্ট → React
- ফুল টাইম → full-time, পার্ট টাইম → part-time, রিমোট → remote
- জুনিয়র → entry, সিনিয়র → senior, মধ্যম → mid
- হাজার → 1000 (multiply), লাখ → 100000 (multiply)

Query: "{query}"

JSON:"""

        # Get response from Gemini
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        
        # Parse the JSON response
        response_text = response.text.strip()
        
        # Clean up potential markdown formatting
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        parsed_data = json.loads(response_text.strip())
        
        # Ensure original_query is set
        if "original_query" not in parsed_data or not parsed_data["original_query"]:
            parsed_data["original_query"] = query
        
        # Create ParsedFilters object
        filters = ParsedFilters(**parsed_data)
        
        # Log successful parsing with language detection
        language_info = f" (Language: {filters.detected_language})" if filters.detected_language else ""
        logger.info(f"Successfully parsed multilingual query with Gemini{language_info}: {filters}")
        return filters
        
    except Exception as e:
        logger.error(f"Error parsing query with Gemini: {str(e)}")
        logger.info("Falling back to rule-based parser")
        return parse_query_rule_based(query)

def parse_query(query: str) -> ParsedFilters:
    """
    Parse natural language query into structured filters using Gemini LLM.
    Falls back to rule-based parsing if Gemini fails.
    """
    return parse_query_with_gemini(query)

def parse_query_rule_based(query: str) -> ParsedFilters:
    """
    Rule-based query parser using regex patterns.
    Used as fallback when Gemini LLM is unavailable.
    """
    query_lower = query.lower()
    
    # Initialize filters
    filters = ParsedFilters(
        intent="job_search",
        keywords=[],
        location=None,
        geo_radius_km=None,
        salary_min=None,
        salary_max=None,
        employment_type=None,
        experience_level=None,
        skills=[],
        category=None,
        status="active"
    )

    # Extract keywords (remaining meaningful words after parsing other fields)
    keywords = []
    query_words = query.split()
    for word in query_words:
        word_clean = re.sub(r'[^\w\s]', '', word.lower())
        if len(word_clean) > 2 and word_clean not in ['the', 'and', 'with', 'for', 'job', 'jobs', 'work', 'role', 'position']:
            keywords.append(word_clean)

    # Detect location (cities in Bangladesh and other common locations)
    cities = [
        "Dhaka", "Chittagong", "Sylhet", "Rajshahi", "Khulna", "Barisal", "Rangpur", "Mymensingh",
        "Cumilla", "Gazipur", "Narayanganj", "Jessore", "Bogra", "Dinajpur", "Pabna", "Comilla",
        "New York", "London", "Toronto", "Sydney", "Dubai", "Singapore", "Bangalore", "Mumbai"
    ]
    for city in cities:
        if city.lower() in query_lower:
            filters.location = city
            break

    # Detect geo radius (e.g., "within 2km", "2 kilometer radius")
    radius_patterns = [
        r"within\s+(\d+)\s*(?:km|kilometer|kilometres)",
        r"(\d+)\s*(?:km|kilometer|kilometres)\s+radius",
        r"radius\s+of\s+(\d+)\s*(?:km|kilometer|kilometres)"
    ]
    for pattern in radius_patterns:
        match = re.search(pattern, query_lower)
        if match:
            filters.geo_radius_km = int(match.group(1))
            break

    # Detect skills and technologies
    skills_db = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin",
        "React", "Angular", "Vue", "Node.js", "Express", "FastAPI", "Django", "Flask", "Spring", "Laravel",
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "OpenCV",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Jenkins", "Git", "MongoDB", "PostgreSQL", "MySQL", "Redis",
        "Machine Learning", "AI", "Data Science", "DevOps", "Frontend", "Backend", "Full-stack", "Mobile"
    ]
    for skill in skills_db:
        if skill.lower() in query_lower:
            filters.skills.append(skill)

    # Detect salary ranges (e.g., "40k-60k", "40000 to 60000", "minimum 50k salary")
    salary_patterns = [
        r"(\d+)[kK]?\s*[-–to]+\s*(\d+)[kK]?",  # Range: 40k-60k, 40-60k
        r"(\d+)k?\s*-\s*(\d+)k?",  # Simple range: 40-60
        r"salary\s+(\d+)[kK]?\s*[-–to]+\s*(\d+)[kK]?",  # salary 40k-60k
        r"minimum\s+(\d+)[kK]?\s+salary",  # minimum 50k salary
        r"(\d+)[kK]?\s+minimum",  # 50k minimum
    ]
    
    for pattern in salary_patterns:
        match = re.search(pattern, query_lower)
        if match:
            val1 = int(match.group(1))
            # Check if it's a range or minimum
            if len(match.groups()) > 1 and match.group(2):
                val2 = int(match.group(2))
                # Apply k multiplier if present
                if 'k' in match.group(0).lower():
                    val1 *= 1000
                    val2 *= 1000
                filters.salary_min = min(val1, val2)
                filters.salary_max = max(val1, val2)
            else:
                # Minimum salary only
                if 'k' in match.group(0).lower():
                    val1 *= 1000
                filters.salary_min = val1
            break

    # Detect employment type
    employment_types = {
        "full-time": ["full-time", "fulltime", "permanent", "full time"],
        "part-time": ["part-time", "parttime", "part time"],
        "contract": ["contract", "contractor", "freelance", "consulting"],
        "remote": ["remote", "work from home", "wfh", "telecommute"]
    }
    
    for emp_type, keywords_list in employment_types.items():
        for keyword in keywords_list:
            if keyword in query_lower:
                filters.employment_type = emp_type
                break
        if filters.employment_type:
            break

    # Detect experience level
    experience_levels = {
        "entry": ["entry", "junior", "beginner", "fresher", "graduate", "intern"],
        "mid": ["mid", "intermediate", "experienced", "senior", "lead"],
        "senior": ["senior", "principal", "architect", "manager", "director", "head"]
    }
    
    for level, keywords_list in experience_levels.items():
        for keyword in keywords_list:
            if keyword in query_lower:
                filters.experience_level = level
                break
        if filters.experience_level:
            break

    # Detect job categories
    categories = {
        "Software Engineering": ["software", "developer", "programmer", "engineer", "coding"],
        "Data Science": ["data science", "data scientist", "analytics", "data analyst"],
        "AI/ML": ["ai", "artificial intelligence", "machine learning", "ml", "deep learning"],
        "DevOps": ["devops", "deployment", "infrastructure", "cloud"],
        "Design": ["designer", "ui", "ux", "graphic", "creative"],
        "Marketing": ["marketing", "digital marketing", "content", "social media"],
        "Sales": ["sales", "business development", "account manager"],
        "Finance": ["finance", "accounting", "financial analyst"],
        "HR": ["human resources", "hr", "recruiter", "talent acquisition"],
        "Education": ["teacher", "tutor", "instructor", "professor", "education"]
    }
    
    for category, keywords_list in categories.items():
        for keyword in keywords_list:
            if keyword in query_lower:
                filters.category = category
                break
        if filters.category:
            break

    # Filter out detected terms from keywords to avoid duplication
    detected_terms = []
    if filters.location:
        detected_terms.append(filters.location.lower())
    if filters.employment_type:
        detected_terms.extend(employment_types[filters.employment_type])
    if filters.experience_level:
        detected_terms.extend(experience_levels[filters.experience_level])
    if filters.skills:
        detected_terms.extend([skill.lower() for skill in filters.skills])
    if filters.category:
        detected_terms.extend([cat.lower() for cat in categories[filters.category]])

    # Keep only keywords that weren't detected as specific filters
    final_keywords = []
    for keyword in keywords:
        if keyword not in detected_terms and not any(term in keyword for term in detected_terms):
            final_keywords.append(keyword)
    
    filters.keywords = final_keywords[:5]  # Limit to top 5 keywords

    return filters