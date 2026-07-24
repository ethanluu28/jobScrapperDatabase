"""SQLite storage layer for scraped job postings.
"""
from contextlib import contextmanager
import pandas as pd

import psycopg2
import psycopg2.extras


# Schema used to populate columns
SCHEMA = """
    CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_url TEXT NOT NULL UNIQUE,
    site TEXT,
    title TEXT,
    company TEXT,
    location TEXT,
    is_remote BOOLEAN,
    job_type TEXT,
    min_amount DOUBLE PRECISION,
    max_amount DOUBLE PRECISION,
    currency TEXT,
    date_posted TEXT,
    date_scraped TEXT DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    status TEXT DEFAULT 'new'
    )
"""


@contextmanager
def get_conn():
    # Yielding postregSQL connection now

    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="jobtracker",
        user="postgres",
        password="postgres",
        cursor_factory=psycopg2.extras.DictCursor
    )

    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    
    finally:
        # always close connections 
        conn.close()



def init_db():
    # Create the jobs table if it doesn't exist yet

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(SCHEMA)


def upsert_jobs(df):
    # Insert new jobs from a JobSpy DataFrame, skipping ones already in the db.

    if df is None or df.empty:
        return 0
    # Map schema fields to exact columns
    columns_to_insert = [
        "job_url", "site", "title", "company", "location", "is_remote",
        "job_type", "min_amount", "max_amount", "currency", "date_posted",
        "description"
    ]
    # Filter available columns from dataframe
    available_cols = [col for col in columns_to_insert if col in df.columns]

    # Build SQL statment based on present columns
    placeholders = ", ".join(["%s"] * len(available_cols))
    col_names_str = ", ".join(available_cols)
    sql = f"INSERT INTO jobs ({col_names_str}) VALUES ({placeholders}) ON CONFLICT (job_url) DO NOTHING"

    # Process each row to get count
    totalInserted = 0
    with get_conn() as conn:
        cursor = conn.cursor()

        for _, row in df[available_cols].iterrows():
            # Convert pandas NaN values to Python None 
            rowDict = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
            values = tuple(rowDict[col] for col in available_cols)

            cursor.execute(sql, values)
            # 1 if inserted, 0 if ignored
            if cursor.rowcount > 0:
                totalInserted += cursor.rowcount
    
    return totalInserted


def get_jobs(keyword=None, company=None, remote_only=False, status="all", limit=50, offset=0):
    # Gets job data from table with filters applied
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if keyword:
        query += " AND (title ILIKE %s OR description ILIKE %s)"
        like_term = f"%{keyword}%"
        params.extend([like_term, like_term])

    if company:
        query += " AND company ILIKE %s"
        params.append(f"%{company}%")

    if remote_only:
        query += " AND is_remote = TRUE"

    if status != "all":
        query += " AND status = %s"
        params.append(status)

    query += " ORDER BY date_posted DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with get_conn() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    return df

def get_filtered_jobs_count(keyword="", company="", remote_only=False, status="all"):
    # Reg SQL count query
    query = "SELECT COUNT(*) FROM jobs WHERE 1=1"
    params = []
    
    # Inject identical user filter selections
    if keyword:
        query += " AND (title ILIKE %s OR description ILIKE %s)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if company:
        query += " AND company ILIKE %s"
        params.append(f"%{company}%")
    if remote_only:
        query += " AND is_remote = TRUE"
    if status != "all":
        query += " AND status = %s"
        params.append(status)

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        
    # Return the simple integer count
    return result[0] if result else 0


def update_job_status(job_id, status):
    # Updating job metrics
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""UPDATE jobs SET status=%s WHERE id=%s""", (status, job_id))


def get_metrics():
    # Getting metrics
    with get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM jobs")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'new'")
        new = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'applied'")
        applied = cursor.fetchone()[0]

    return {
        "total": total,
        "new": new,
        "applied": applied
    }

def job_count():
    # Return the total number of rows in the jobs table
    
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs")
        result = cursor.fetchone()

        return result[0] if result else 0

