"""Local web dashboard for the job tracker. See README.md Step 5.

Once implemented, run with:
    streamlit run app.py
Opens in your browser at http://localhost:8501
"""
import pandas as pd
import streamlit as st

from db import get_conn, init_db, upsert_jobs
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


# Build filtered query
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

if status_filter != "all":
    query += " AND status = ?"
    params.append(status_filter)

query += " ORDER BY date_posted DESC LIMIT ?"
params.append(limit)

# Load database payload into a Pandas DataFrame
with get_conn() as conn:
    df = pd.read_sql_query(query, conn, params=params)

# Getting Metrics
with get_conn() as conn:
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM jobs")
    totalCount = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'new'")
    newCount = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'applied'")
    appliedCount = cursor.fetchone()[0]

# Displaying metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Cached Jobs", totalCount)
col2.metric("New Openings", newCount)
col3.metric("Applications Submitted", appliedCount)


st.divider()

# ---------- Job list ----------
# TODO: if df.empty: st.info(...)
# else: for _, row in df.iterrows():
#   with st.container(border=True):
#       render title as a markdown link (row["job_url"]), company/location,
#       remote/onsite tag, site, date_posted, and a
#       st.selectbox(..., STATUSES, key=f"status_{row['id']}") for status
#       -- if the selected value differs from row["status"], UPDATE the db
#       and call st.rerun()
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
                    with get_conn() as conn:
                        conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (new_status, row['id']))
                    st.toast(f"Updated job #{row['id']} to {new_status}!")
                    st.rerun()