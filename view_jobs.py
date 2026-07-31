"""Browse and manage your scraped job listings from the command line.
See README.md Step 4.

Target usage once implemented:
    python view_jobs.py list
    python view_jobs.py list --keyword python --remote
    python view_jobs.py list --company Google --status new
    python view_jobs.py mark 14 applied
"""
import argparse
from db import get_conn
import pandas as pd


def list_jobs(keyword=None, company=None, remote_only=False, status=None, limit=30):
    # Print jobs matching the given filters, newest first.

    query = """
        WITH ranked_jobs AS (
            SELECT *,
            DENSE_RANK() OVER (
                PARTITION BY company ORDER BY COALESCE(max_amount, min_amount) DESC NULLS LAST
            ) AS salary_rank,
            COUNT(*) OVER (PARTITION BY company) AS total_company_jobs
            FROM jobs
        )
        SELECT * FROM ranked_jobs WHERE 1=1
        """
    params = []

    # Dynamically appending to SQL filter safely
    if keyword:
        query += " AND (title ILIKE %s OR description ILIKE %s)"
        like_term = f"%{keyword}%"
        params.extend([like_term, like_term])
    
    if company:
        query += " AND company ILIKE %s"
        params.append(f"%{company}%")
    
    if remote_only:
        query += " AND is_remote = TRUE"
    
    if status:
        query += " AND status = %s"
        params.append(status)
    
    query += " ORDER BY date_posted DESC LIMIT %s"
    params.append(limit)

    # Query database with context from params
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    if not rows:
        print("No job found using filter specified")
        return
    
    # Setting up clean output terminal 
    print(f"\n{'ID':<5} | {'TITLE':<30} | {'SALARY':<20} | {'RANK':<8} | {'COMPANY':<20} | {'STATUS':<10} | {'POSTED'}")    
    print("-" * 120)
    
    for row in rows:
        # Truncate strings with ellipses to keep rows strictly on a single line
        title = (row["title"][:27] + "...") if row["title"] and len(row["title"]) > 30 else (row["title"] or "")
        company_name = (row["company"][:17] + "...") if row["company"] and len(row["company"]) > 20 else (row["company"] or "")
        # Format salary
        min_amt = int(row['min_amount']) if pd.notna(row['min_amount']) else None
        max_amt = int(row['max_amount']) if pd.notna(row['max_amount']) else None
        if min_amt and max_amt:
            salary_str = f"${min_amt:,}-${max_amt:,}"
        elif min_amt:
            salary_str = f"${min_amt:,}+"
        elif max_amt:
            salary_str = f"Up to ${max_amt:,}"
        else:
            salary_str = "Not Listed"

        # Format Rank Column without emojis
        if pd.notna(row['min_amount']) or pd.notna(row['max_amount']):
            rank_str = f"#{int(row['salary_rank'])} out of {int(row['total_company_jobs'])}"
        else:
            rank_str = "No Rank"
        
        # Print formatted aligned to header positions
        print(f"{row['id']:<5} | {title:<30} | {salary_str:<22} | {rank_str:<15} | {company_name:<20} | {row['status']:<10} | {row['date_posted'] or 'Unknown'}")
    print()


def mark_status(job_id, status):
    """Update a single job's status column.
    Check cursor.rowcount to tell the user if no job matched that id.
    """
    query = "UPDATE jobs SET status = %s WHERE id = %s"

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (status, job_id))

    if cursor.rowcount == 0:
        print(f"Error: No job entry found matching ID {job_id}")
    else:
        print(f"Job {job_id} marked as '{status}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Browse and manage scraped job listings.")
    sub = parser.add_subparsers(dest="cmd")

    # Defining valid choices
    STATUS_CHOICES = ["new", "viewed", "applied", "rejected", "archived"]

    # Adding the 'list' subcommand params
    list_parser = sub.add_parser("list", help="List filtered jobs from the database")
    list_parser.add_argument("--keyword", type=str, help="Search text in title or description")
    list_parser.add_argument("--company", type=str, help="Filter by company name")
    list_parser.add_argument("--remote", action="store_true", help="Filter for remote jobs only")
    list_parser.add_argument("--status", type=str, choices=STATUS_CHOICES, help="Filter by workflow status")
    list_parser.add_argument("--limit", type=int, default=30, help="Maximum number of rows to return (default: 30)")

    # Setup the 'mark' subcommand params
    mark_parser = sub.add_parser("mark", help="Update lifecycle status")
    mark_parser.add_argument("job_id", type=int, help="Numerical ID of the listing")
    mark_parser.add_argument("status", choices=["new", "viewed", "applied", "rejected", "archived"], help="New status value")

    # Parse user inputs
    args = parser.parse_args()

    # Routes user inputs to logic functions
    if args.cmd == "list":
        list_jobs(
            keyword=args.keyword,
            company=args.company,
            remote_only=args.remote,
            status=args.status,
            limit=args.limit
        )
    elif args.cmd == "mark":
        mark_status(job_id=args.job_id, status=args.status)
    else:
        parser.print_help()