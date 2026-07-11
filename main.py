"""Run your searches and save results into jobs.db. See README.md Step 3.

Once implemented, run with:
    python main.py
"""
from db import init_db, upsert_jobs, job_count
from scraper import run_searches

# Defining searches here, based off dicts
# sites can include: "indeed", "linkedin", "google", "glassdoor", "zip_recruiter"

SEARCHES = [
    dict(
        search_term="software engineer",
        location="Los Angeles, CA",
        sites=("indeed", "linkedin", "google"),
        results_wanted=25,
        hours_old=72
    )
]


def main():

    init_db()
    df = run_searches(SEARCHES)
    scrapedCount = len(df)
    newCount = upsert_jobs(df)
    totalCount = job_count()

    print(f"Jobs scraped this run: {scrapedCount}")
    print(f"New jobs added: {newCount}")
    print(f"Total jobs in db: {totalCount}")


if __name__ == "__main__":
    main()
