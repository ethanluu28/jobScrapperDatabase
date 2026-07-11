# Job Tracker

Scrapes software engineering job postings (LinkedIn, Indeed, Google, Glassdoor,
ZipRecruiter) using JobSpy, saves them to a local SQLite database, and lets you
browse/filter them from the command line or a web dashboard.

## Setup

Use Python 3.11 or 3.12 as numpy doesn't have prebuilt wheels for newer Python
versions yet, which causes install errors.

```bash
py -3.12 -m venv venv
venv\Scripts\activate   # windows
pip install -r requirements.txt
```

## Usage

**Scrape jobs:**

Edit the `SEARCHES` list in `main.py` (search terms, locations, sites), then:

```bash
python main.py
```

This creates `jobs.db` automatically on first run and adds any new postings to
it. Re-running it later only adds jobs you don't already have — duplicates
(matched by URL) are skipped.

**Browse results:**

Web dashboard:
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`. Filter by keyword, company, remote, or
status, and change a job's status from a dropdown on each listing. There's
also a "Run scrape now" button in the sidebar, so you don't need `main.py` at
all if you'd rather do everything from the browser.

Command line:
```bash
python view_jobs.py list
python view_jobs.py list --keyword python --remote
python view_jobs.py list --company Google --status new
python view_jobs.py mark 14 applied
```

## Files

| File | Purpose |

| `db.py` | SQLite schema and connection handling. Dedupes on `job_url`. |
| `scraper.py` | Wraps JobSpy, runs one or more searches with a pause between them. |
| `main.py` | Defines your searches and runs a scrape from the terminal. |
| `view_jobs.py` | Command-line browser/filter for saved jobs. |
| `app.py` | Streamlit web dashboard — same data, browser UI. |

## Database

`jobs.db` is a plain SQLite file, created automatically the first time
`main.py` or `app.py` runs — no manual setup needed. It always lives in the
project folder itself, regardless of where you run commands from. You can
also open it directly with a tool like
[DB Browser for SQLite](https://sqlitebrowser.org/) if you want to poke
around outside the app.

## Notes on LinkedIn / Google Jobs

- LinkedIn rate-limits scrapers and its Terms of Service prohibit automated
  scraping. This project only hits public non-logged-in search results and
  pauses between searches, but frequent/high-volume scraping can still get
  temporarily blocked.
- "Google Jobs" isn't a separate site to scrape — it's postings aggregated
  from sites using `schema.org/JobPosting` markup, shown inside Google
  Search. JobSpy handles this via a search phrase (`google_search_term`);
  results can be inconsistent.
- Keep `results_wanted` and run frequency modest — there's no benefit to
  scraping more than you'll read, and it lowers your odds of getting blocked.

