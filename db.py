"""SQLite storage layer for scraped job postings.
"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
import pandas as pd

DB_PATH = Path(__file__).parent / "jobs.db"

# Schema used to populate columns
SCHEMA = """
    CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_url TEXT NOT NULL UNIQUE,
    site TEXT,
    title TEXT,
    company TEXT,
    location TEXT,
    is_remote INTEGER,
    job_type TEXT,
    min_amount REAL,
    max_amount REAL,
    currency TEXT,
    date_posted TEXT,
    date_scraped TEXT DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    status TEXT DEFAULT 'new'
    )
"""


@contextmanager
def get_conn():
    # Yield a sqlite3 connection, committing on success and always closing

    conn = sqlite3.connect(DB_PATH)

    try:
        conn.row_factory = sqlite3.Row
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
        conn.executescript(SCHEMA)


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
    placeholders = ", ".join(["?"] * len(available_cols))
    col_names_str = ", ".join(available_cols)
    sql = f"INSERT OR IGNORE INTO jobs ({col_names_str}) VALUES ({placeholders})"

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


def get_jobs(keyword=None, company=None, remote_only=False, status="all", limit=50):
    # Gets job data from table with filters applied
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if keyword:
        query += " AND (title LIKE ? OR description LIKE ?)"
        like_term = f"%{keyword}%"
        params.extend([like_term, like_term])

    if company:
        query += " AND company LIKE ?"
        params.append(f"%{company}%")

    if remote_only:
        query += " AND is_remote = 1"

    if status != "all":
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY date_posted DESC LIMIT ?"
    params.append(limit)

    with get_conn() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    return df

def update_job_status(job_id, status):
    # Updating job metrics
    with get_conn() as conn:
        conn.execute(
            """UPDATE jobs SET status=? WHERE id=?""",
            (status, job_id)
        )

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

