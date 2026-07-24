"""Local web dashboard for the job tracker. See README.md Step 5.

Run with:
    streamlit run app.py
Opens in your browser at http://localhost:8501
"""
import pandas as pd
import streamlit as st

from db import init_db, upsert_jobs, get_jobs, update_job_status, get_metrics, get_filtered_jobs_count
from scraper import run_searches

def resetPage():
    st.session_state.page = 1

STATUSES = ["new", "viewed", "applied", "rejected", "archived"]

st.set_page_config(page_title="Job Tracker", page_icon="💼", layout="wide")
init_db()

st.title("💼 Job Tracker")

# Getting metrics for sidebar
metrics = get_metrics()


# Sidebar: filters and scrape trigger 
with st.sidebar:
    st.header("Filters")
    keyword = st.text_input("Keyword search (title/desc)", on_change=resetPage)
    company = st.text_input("Company name", on_change=resetPage)
    remote_only = st.checkbox("Remote entries only", on_change=resetPage)
    status_filter = st.selectbox("Workflow status", ["all"] + STATUSES, on_change=resetPage)

    # Getting direct query count for current filter
    total_records = get_filtered_jobs_count(
        keyword=keyword, company=company, remote_only=remote_only, status=status_filter
    )

    # Safe initialization to track page number
    if "page" not in st.session_state:
        st.session_state["page"] = 1

    limit = st.slider("Max records to display", min_value=10, max_value=200, value = 50, step = 10)

    col1, col2 = st.columns(2)
    TOTAL_PAGE = (total_records // limit) + 1

    with col1:
        if st.button("⬅️ Previous", disabled=(st.session_state.page == 1)):
            st.session_state.page -= 1
            st.rerun()  # Forces immediate visual update

    with col2:
        if st.button("Next ➡️", disabled=(st.session_state.page == TOTAL_PAGE)):
            st.session_state.page += 1
            st.rerun()

    # Display the current page state
    st.write(f"### Viewing Page {st.session_state.page} of {TOTAL_PAGE}")

    # Creating features
    st.divider()
    st.header("Scrape")
    scrape_filter = st.text_input("Job Search Entry")
    location_input = st.text_input("Location", value="Los Angeles, CA")
    result_count = st.number_input("Results Wanted", min_value=1, max_value=100, value=25)
    if st.button("Run scrape now", type="primary"):
        if not scrape_filter.strip():
            st.error("Error: Job Search Entry cannot be empty!")
        else:
            with st.spinner("Scraping job boards via Jobspy (using safe timeouts)..."):
                SEARCHES = [
                    dict(
                            search_term=scrape_filter.strip(),
                            location=location_input.strip(),
                            sites=("indeed", "linkedin", "google"),
                            results_wanted=int(result_count),
                            hours_old=72
                        )
                ]
                df_scraped = run_searches(SEARCHES)
                newCount = upsert_jobs(df_scraped)
            st.success(f"Scrape finished! Added {newCount} brand new unique job listings.")
            st.rerun()


offset = (st.session_state["page"] - 1) * limit

df = get_jobs(
    keyword=keyword,
    company=company,
    remote_only=remote_only,
    status=status_filter,
    limit=limit,
    offset=offset
)

# Getting Metrics
metrics = get_metrics()

# Displaying metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Cached Jobs", metrics["total"])
col2.metric("New Openings", metrics["new"])
col3.metric("Applications Submitted", metrics["applied"])


st.divider()

# Job list with formating
if df.empty:
    st.info("No job listings match your current sidebar query parameters.")
else:
    for _, row in df.iterrows():
        # Build individual cleanly bounded display cards
        with st.container(border=True):
            # Layout splitting information from the interactive dropdown controls
            info_col, action_col = st.columns([4, 1])
            
            with info_col:
                # Make the title clickable
                st.markdown(f"### [{row['title'] or 'Untitled opening'}]({row['job_url']})")
                
                # Metadata line with safety fallbacks
                comp = row['company'] or "Unknown Company"
                loc = row['location'] or "Location Unspecified"
                remote_tag = "🌐 Remote" if row['is_remote'] else "🏢 Onsite/Hybrid"
                site_source = (row['site'] or "Direct").upper()
                posted_time = row['date_posted'] or "Unknown date"
                
                st.markdown(f"**{comp}** | {loc} | {remote_tag} | *Source: {site_source}* | *Posted: {posted_time}*")
                
                # Optional snippet expander for descriptions
                if row['description']:
                    with st.expander("Show detailed text summary"):
                        st.write(row['description'])
            
            with action_col:
                # Safeguard string alignment before indexing layout index variables
                current_status = row['status'] if row['status'] in STATUSES else "new"
                status_idx = STATUSES.index(current_status)
                
                # Interactive state modifier dropdown
                new_status = st.selectbox(
                    "Update Status",
                    STATUSES,
                    index=status_idx,
                    key=f"status_{row['id']}"
                )
                
                # If the selected value differs from row["status"], UPDATE the db and reload
                if new_status != row['status']:
                    update_job_status(row['id'], new_status)
                    st.toast(f"Updated job #{row['id']} to {new_status}!")
                    st.rerun()