"""Local web dashboard for the job tracker. See README.md Step 5.

Run with:
    streamlit run app.py
Opens in your browser at http://localhost:8501
"""
import pandas as pd
import streamlit as st

from db import init_db, upsert_jobs, get_jobs, update_job_status, get_metrics
from scraper import run_searches
from main import SEARCHES

STATUSES = ["new", "viewed", "applied", "rejected", "archived"]

st.set_page_config(page_title="Job Tracker", page_icon="💼", layout="wide")
init_db()

st.title("💼 Job Tracker")

# Sidebar: filters and scrape trigger 
with st.sidebar:
    st.header("Filters")
    keyword = st.text_input("Keyword search (title/desc)")
    company = st.text_input("Company name")
    remote_only = st.checkbox("Remote entries only")
    status_filter = st.selectbox("Workflow status", ["all"] + STATUSES)
    limit = st.slider("Max records to display", min_value=10, max_value=200, value = 50, step = 10)

    # Creating features
    st.divider()
    st.header("Scrape")
    if st.button("Run scrape now", type="primary"):
        with st.spinner("Scraping job boards via Jobspy (using safe timeouts)..."):
            df_scraped = run_searches(SEARCHES)
            newCount = upsert_jobs(df_scraped)
        st.success(f"Scrape finished! Added {newCount} brand new unique job listings.")
        st.rerun()


df = get_jobs(
    keyword=keyword,
    company=company,
    remote_only=remote_only,
    status=status_filter,
    limit=limit
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
                remote_tag = "🌐 Remote" if row['is_remote'] == 1 else "🏢 Onsite/Hybrid"
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