from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from db import upsert_jobs
from scraper import run_searches
import pandas as pd
import pendulum

def scrape_data_engineer_jobs(configs, pause_seconds=5):
    df = run_searches(configs, pause_seconds=pause_seconds)
    return df.to_dict('records')

def update_database(ti):
    records = ti.xcom_pull(task_ids='Complete_Job_Scrape')
    df = pd.DataFrame(records)
    newCount = upsert_jobs(df)
    print(f"New jobs added: {newCount}")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026, 4, 8, tzinfo=pendulum.timezone("America/Los_Angeles")),
    'email': ['eluunarmoon@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

dag = DAG(
    'Job_Scraper_Scheduler',
    default_args = default_args,
    description = "Daily job scrape for eng jobs",
    schedule = "0 8 * * *",
    #schedule = "5 6 * * *",
    catchup = False
)

SEARCHES = [
    dict(
        search_term="software engineer",
        location="Los Angeles, CA",
        sites=("indeed", "linkedin", "google"),
        results_wanted=25,
        hours_old=72
    )
]

scrape_task = PythonOperator(
    task_id="Complete_Job_Scrape",
    python_callable=scrape_data_engineer_jobs,
    op_kwargs={'configs': SEARCHES, 'pause_seconds': 5},
    dag=dag
)

update_db_task = PythonOperator(
    task_id="Update_Database",
    python_callable=update_database,
    dag=dag
)

scrape_task >> update_db_task