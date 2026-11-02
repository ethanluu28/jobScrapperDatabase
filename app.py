"""Local web dashboard for the job tracker. See README.md Step 5.

Run with:
    streamlit run app.py
Opens in your browser at http://localhost:8501
"""
import pandas as pd
import streamlit as st
from math import ceil

#from db import init_db, upsert_jobs, get_jobs, update_job_status, get_metrics, get_filtered_jobs_count
from scraper import run_searches
import requests


API_URL = "http://localhost:8000/jobs"
STATUSES = ["new", "viewed", "applied", "rejected", "archived"]
st.set_page_config(page_title="Job Tracker", page_icon="💼", layout="wide")

def api(method, path, timeout=10, **kwargs):
    try:
        resp = requests.request(method, f"{API_URL}{path}", timeout=timeout, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else None
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        st.stop()


def filter_params(keyword, company, remote_only, status):
    return {
        "keyword": keyword or None,
        "company": company or None,
        "remote_only": True if remote_only else None,
        "status": None if status == "all" else status,
    }


def resetPage():
    st.session_state.page = 1


if "page" not in st.session_state:
    st.session_state.page = 1


def get_jobs_count_api(
    status: str | None = None,
    company: str | None = None,
    keyword: str | None = None,
    remote_only: bool = False
) -> dict:

    query_params = {
        "status": status,
        "company": company,
        "keyword": keyword,
        "remote_only": remote_only
    }
    try:
        # GET request to API
        response = requests.get(f"{API_URL}/count")
        response.raise_for_status()

        return response.json()


    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to API Server: {e}")
        return {"total": 0}
    


st.title("💼 Job Tracker")

with st.sidebar:
    st.header("Filters")
    if st.button("🔄 Refresh"):
        st.rerun()
    keyword = st.text_input("Keyword search (title/desc)", on_change=resetPage)
    company = st.text_input("Company name", on_change=resetPage)
    remote_only = st.checkbox("Remote entries only", on_change=resetPage)
    status_filter = st.selectbox("Workflow status", ["all"] + STATUSES, on_change=resetPage)

    params = filter_params(keyword, company, remote_only, status_filter)
    total_records = api("GET", "/count", params=params)["total"]

    limit = st.slider("Max records to display", 10, 200, 50, 10, on_change=resetPage)
    TOTAL_PAGE = max(1, ceil(total_records / limit))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Previous", disabled=(st.session_state.page == 1)):
            st.session_state.page -= 1
            st.rerun()
    with col2:
        if st.button("Next ➡️", disabled=(st.session_state.page == TOTAL_PAGE)):
            st.session_state.page += 1
            st.rerun()
    st.write(f"### Viewing Page {st.session_state.page} of {TOTAL_PAGE}")

    st.divider()
    st.header("Scrape")
    scrape_filter = st.text_input("Job Search Entry")
    location_input = st.text_input("Location", value="Los Angeles, CA")
    result_count = st.number_input("Results Wanted", min_value=1, max_value=100, value=25)
    if st.button("Run scrape now", type="primary"):
        if not scrape_filter.strip():
            st.error("Error: Job Search Entry cannot be empty!")
        else:
            with st.spinner("Scraping job boards..."):
                api("POST", "/scrape", timeout=10, json={
                    "search_term": scrape_filter.strip(),
                    "location": location_input.strip(),
                    "results_wanted": int(result_count),
                    "hours_old": 72,
                    "site_name": ["indeed", "linkedin", "google"],
                })
            st.toast("Scrape request completed!")
            st.rerun()

offset = (st.session_state.page - 1) * limit
jobs = api("GET", "/", params={**params, "limit": limit, "offset": offset})
df = pd.DataFrame(jobs)

metrics = api("GET", "/metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Cached Jobs", metrics["total"])
col2.metric("New Openings", metrics["new"])
col3.metric("Applications Submitted", metrics["applied"])
st.divider()

if df.empty:
    st.info("No job listings match your current sidebar query parameters.")
else:
    for _, row in df.iterrows():
        with st.container(border=True):
            info_col, action_col = st.columns([4, 1])

            with info_col:
                st.markdown(f"### [{row['title'] or 'Untitled opening'}]({row['job_url']})")
                comp = row['company'] or "Unknown Company"
                loc = row['location'] or "Location Unspecified"

                min_salary = int(row['min_amount']) if pd.notna(row['min_amount']) else None
                max_salary = int(row['max_amount']) if pd.notna(row['max_amount']) else None
                if min_salary and max_salary:
                    salary = f"💰 \\${min_salary:,}-\\${max_salary:,} |"
                elif min_salary:
                    salary = f"💰 \\${min_salary:,}+ |"
                elif max_salary:
                    salary = f"💰 up to \\${max_salary:,} |"
                else:
                    salary = ""

                remote_tag = "🌐 Remote" if row['is_remote'] else "🏢 Onsite/Hybrid"
                site_source = (row['site'] or "Direct").upper()
                posted = row['date_posted'] or "Unknown date"
                st.markdown(f"**{comp}** | {loc} | {salary} {remote_tag} | *Source: {site_source}* | *Posted: {posted}*")

                if row['description']:
                    with st.expander("Show detailed text summary"):
                        st.write(row['description'])

            with action_col:
                current = row['status'] if row['status'] in STATUSES else "new"
                new_status = st.selectbox("Update Status", STATUSES,
                                          index=STATUSES.index(current),
                                          key=f"status_{row['id']}")
                if new_status != row['status']:
                    api("PATCH", f"/{row['id']}", json={"status": new_status})
                    st.toast(f"Updated job #{row['id']} to {new_status}!")
                    st.rerun()