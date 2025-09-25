from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, PreparedStatement
from cassandra.auth import PlainTextAuthProvider
from typing import List, Dict, Optional
from uuid import UUID
import logging
from app.config import SCYLLA_HOSTS, SCYLLA_PORT, SCYLLA_KEYSPACE
from app.models.job_models import Job, ParsedFilters

logger = logging.getLogger(__name__)

class ScyllaRepository:
    def __init__(self):
        self.cluster = None
        self.session = None
        self.prepared_statements = {}
        self._connect()
        self._create_keyspace()
        self._create_tables()
        self._prepare_statements()

    def _connect(self):
        """Connect to ScyllaDB cluster"""
        try:
            # For production, you might want to add authentication
            # auth_provider = PlainTextAuthProvider(username='username', password='password')
            self.cluster = Cluster(SCYLLA_HOSTS, port=SCYLLA_PORT)
            self.session = self.cluster.connect()
            logger.info(f"Connected to ScyllaDB at {SCYLLA_HOSTS}:{SCYLLA_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to ScyllaDB: {str(e)}")
            raise

    def _create_keyspace(self):
        """Create keyspace if it doesn't exist"""
        try:
            self.session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {SCYLLA_KEYSPACE}
                WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};
            """)
            self.session.set_keyspace(SCYLLA_KEYSPACE)
            logger.info(f"Keyspace {SCYLLA_KEYSPACE} ready")
        except Exception as e:
            logger.error(f"Failed to create keyspace: {str(e)}")
            raise

    def _create_tables(self):
        """Create tables if they don't exist"""
        try:
            # Main jobs table
            self.session.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id UUID PRIMARY KEY,
                    provider_id UUID,
                    title text,
                    description text,
                    category text,
                    city text,
                    country text,
                    latitude double,
                    longitude double,
                    employment_type text,
                    salary_min int,
                    salary_max int,
                    currency text,
                    experience_level text,
                    skills set<text>,
                    status text,
                    is_verified boolean,
                    date_posted timestamp,
                    expiry_date timestamp
                );
            """)

            # Secondary indexes for efficient filtering
            # Note: In production, consider using materialized views instead
            self.session.execute("CREATE INDEX IF NOT EXISTS idx_jobs_city ON jobs (city);")
            self.session.execute("CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs (category);")
            self.session.execute("CREATE INDEX IF NOT EXISTS idx_jobs_employment_type ON jobs (employment_type);")
            self.session.execute("CREATE INDEX IF NOT EXISTS idx_jobs_experience_level ON jobs (experience_level);")
            self.session.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status);")
            
            logger.info("Jobs table and indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise

    def _prepare_statements(self):
        """Prepare frequently used statements for better performance"""
        try:
            self.prepared_statements['insert_job'] = self.session.prepare("""
                INSERT INTO jobs (job_id, provider_id, title, description, category, city, country,
                                  latitude, longitude, employment_type, salary_min, salary_max,
                                  currency, experience_level, skills, status, is_verified, date_posted, expiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)
            
            self.prepared_statements['get_job_by_id'] = self.session.prepare("""
                SELECT * FROM jobs WHERE job_id = ?
            """)
            
            logger.info("Prepared statements created successfully")
        except Exception as e:
            logger.error(f"Failed to prepare statements: {str(e)}")
            raise

    def insert_job(self, job_data: Dict) -> bool:
        """Insert a job into ScyllaDB"""
        try:
            stmt = self.prepared_statements['insert_job']
            self.session.execute(stmt, (
                job_data["job_id"],
                job_data["provider_id"],
                job_data["title"],
                job_data["description"],
                job_data["category"],
                job_data["city"],
                job_data["country"],
                job_data["latitude"],
                job_data["longitude"],
                job_data["employment_type"],
                job_data["salary_min"],
                job_data["salary_max"],
                job_data["currency"],
                job_data["experience_level"],
                set(job_data["skills"]) if job_data["skills"] else set(),
                job_data["status"],
                job_data["is_verified"],
                job_data["date_posted"],
                job_data["expiry_date"],
            ))
            logger.info(f"Inserted job {job_data['job_id']} into ScyllaDB")
            return True
        except Exception as e:
            logger.error(f"Failed to insert job: {str(e)}")
            return False

    def get_job_by_id(self, job_id: UUID) -> Optional[Dict]:
        """Get a job by its ID"""
        try:
            stmt = self.prepared_statements['get_job_by_id']
            result = self.session.execute(stmt, [job_id])
            row = result.one()
            if row:
                return dict(row._asdict())
            return None
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {str(e)}")
            return None

    def filter_jobs(self, filters: ParsedFilters, limit: int = 100) -> List[Dict]:
        """Filter jobs based on parsed filters"""
        try:
            # Build WHERE clause based on available filters
            where_conditions = []
            parameters = []
            
            # Always filter by status
            where_conditions.append("status = ?")
            parameters.append(filters.status or "active")
            
            if filters.location:
                where_conditions.append("city = ?")
                parameters.append(filters.location)
            
            if filters.category:
                where_conditions.append("category = ?")
                parameters.append(filters.category)
            
            if filters.employment_type:
                where_conditions.append("employment_type = ?")
                parameters.append(filters.employment_type)
            
            if filters.experience_level:
                where_conditions.append("experience_level = ?")
                parameters.append(filters.experience_level)
            
            # Build the query
            base_query = "SELECT * FROM jobs"
            if where_conditions:
                query = f"{base_query} WHERE {' AND '.join(where_conditions)} ALLOW FILTERING"
            else:
                query = f"{base_query} LIMIT {limit}"
            
            # Add limit
            if where_conditions:
                query += f" LIMIT {limit}"
            
            stmt = SimpleStatement(query)
            rows = self.session.execute(stmt, parameters)
            
            results = []
            for row in rows:
                job_data = dict(row._asdict())
                
                # Apply salary filters (post-query filtering)
                if filters.salary_min and job_data.get('salary_min'):
                    if job_data['salary_min'] < filters.salary_min:
                        continue
                
                if filters.salary_max and job_data.get('salary_max'):
                    if job_data['salary_max'] > filters.salary_max:
                        continue
                
                # Apply skills filter (post-query filtering)
                if filters.skills and job_data.get('skills'):
                    job_skills = set(job_data['skills']) if job_data['skills'] else set()
                    filter_skills = set(filters.skills)
                    if not filter_skills.intersection(job_skills):
                        continue
                
                results.append(job_data)
            
            logger.info(f"Filtered jobs: found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to filter jobs: {str(e)}")
            return []

    def get_jobs_by_ids(self, job_ids: List[UUID]) -> List[Dict]:
        """Get multiple jobs by their IDs"""
        try:
            if not job_ids:
                return []
            
            # Use IN clause for batch retrieval
            placeholders = ','.join(['?' for _ in job_ids])
            query = f"SELECT * FROM jobs WHERE job_id IN ({placeholders})"
            stmt = SimpleStatement(query)
            rows = self.session.execute(stmt, job_ids)
            
            results = [dict(row._asdict()) for row in rows]
            logger.info(f"Retrieved {len(results)} jobs by IDs")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get jobs by IDs: {str(e)}")
            return []

    def close(self):
        """Close the connection"""
        if self.cluster:
            self.cluster.shutdown()

# Singleton instance
_scylla_repo = None

def get_scylla_repository() -> ScyllaRepository:
    """Get singleton ScyllaDB repository instance"""
    global _scylla_repo
    if _scylla_repo is None:
        _scylla_repo = ScyllaRepository()
    return _scylla_repo

# Legacy functions for backward compatibility
def insert_job(job_data: Dict) -> bool:
    """Legacy function - use get_scylla_repository().insert_job() instead"""
    return get_scylla_repository().insert_job(job_data)

def filter_jobs(filters: Dict) -> List[Dict]:
    """Legacy function - use get_scylla_repository().filter_jobs() instead"""
    # Convert dict filters to ParsedFilters for compatibility
    from app.models.job_models import ParsedFilters
    parsed_filters = ParsedFilters(**filters)
    return get_scylla_repository().filter_jobs(parsed_filters)
