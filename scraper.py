"""Wraps JobSpy to run one or more searches.

JobSpy scrapes LinkedIn, Indeed, Google, Glassdoor, and ZipRecruiter and
returns a pandas DataFrame per search: https://github.com/speedyapply/JobSpy
"""
import time
import pandas as pd
from jobspy import scrape_jobs


def run_search(search_term, location, sites=("indeed", "linkedin", "google"),
                results_wanted=20, hours_old=72, google_search_term=None,
                country_indeed="USA", is_remote=False):
    # Run a single search across the given sites. Returns a DataFrame (possibly empty).

    siteNames = list(sites)
    try:
        # Call scrape_jobs passing through these params
        df = scrape_jobs(
            site_name=siteNames,
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            google_search_term=google_search_term or f"{search_term} jobs near {location}",
            country_indeed=country_indeed,
            is_remote=is_remote,
            linkedin_fetch_description=True if "linkedin" in siteNames else False
        )
        # Error checking if None
        if df is None:
            print("Jobsy returned none, returning empty dataframe")
            return pd.DataFrame()
      
        print(f"Search complete, found {len(df)} total records")
        return df
    
    except Exception as e:
        print(f"Error in Jobspy scrape {e}, returning")
        return pd.DataFrame()



def run_searches(configs, pause_seconds=5):
    # Run multiple search configs sequentially with a pause between them.
    # The pause matters most for LinkedIn, which rate-limits aggressively per IP.
    # configs: list of dicts of kwargs accepted by run_search().

    successfulScrapes = []

    for cfg in configs:
        
      try:
          df = run_search(**cfg)
          if df is not None and not df.empty:
              successfulScrapes.append(df)
      except Exception as e:
        print(f"Error scraping at '{cfg.get('search_term')}': {e}")
        
      time.sleep(pause_seconds)

    if not successfulScrapes:
        print("Found 0 jobs in all Scrapper run searches")
        return pd.DataFrame()

    # Removing duplicates
    combinedDF = pd.concat(successfulScrapes, ignore_index=True)

    if "job_url" in combinedDF.columns:
      initial_count = len(combinedDF)
      combinedDF = combinedDF.drop_duplicates(subset="job_url")
      print(f"Scraper run finished: Found {len(combinedDF)} unique jobs (Deduplicated {initial_count - len(combinedDF)} overlaps).")
      
    return combinedDF