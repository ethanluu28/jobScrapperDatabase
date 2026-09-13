from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import Job
from schemas import JobResponse, JobStatusUpdate, ScrapeRequest
from sqlalchemy import select

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scraper import run_searches
from db import upsert_jobs


router = APIRouter()

@router.get("/", response_model=list[JobResponse])
def list_jobs(status: str | None = None, company: str | None = None,
              limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    # Query entire list with specified parameters

    # Apply status/company filters
    statement = select(Job)

    if status:
        statement = statement.where(Job.status.ilike(f"%{status}%"))
    if company:
        statement = statement.where(Job.company.ilike(f"%{company}%"))

    # Apply offset/limits
    statement = statement.order_by(Job.date_scraped.desc()).offset(offset).limit(limit)
    jobs = db.scalars(statement).all()

    return jobs

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    # Display Clicked Job

    statement = select(Job)

    statement = statement.where(Job.id == job_id)
    job = db.scalars(statement).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )

    return job

@router.post("/scrape")
def trigger_scrape(payload: ScrapeRequest):

    SEARCHES = [
        dict(
            search_term=payload.search_term,
            location=payload.location,
            sites=payload.site_name,
            results_wanted=payload.results_wanted,
            hours_old=payload.hours_old
        )
    ]

    scraped_df = run_searches(configs=SEARCHES)

    upsert_jobs(scraped_df)

    return {"status": "success",
            "processed_jobs": len(scraped_df)} 


@router.patch("/{job_id}", response_model=JobResponse)
def update_status(job_id: int, payload: JobStatusUpdate, db: Session = Depends(get_db)):

    statement = select(Job)
    statement = statement.where(Job.id == job_id)
    db_job = db.scalars(statement).first()

    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )

    update_data = payload.model_dump()

    for key, value in update_data.items():
        setattr(db_job, key, value)

    db.commit()
    db.refresh(db_job)

    return db_job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, db: Session = Depends(get_db)):

    statement = select(Job)
    statement = statement.where(Job.id == job_id)
    db_job = db.scalars(statement).first()

    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )

    db.delete(db_job)
    db.commit()

    return None