from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import List

class JobResponse(BaseModel):
    id: int
    job_url: str
    site: str | None = None
    title: str | None = None
    company: str | None = None
    location: str | None = None
    is_remote: bool | None = None
    job_type: str | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    currency: str | None = None
    status: str
    date_posted: str | None = None
    date_scraped: str
    description: str | None = None

    class Config:
        from_attributes = True

class JobStatusUpdate(BaseModel):
    status: str

class ScrapeRequest(BaseModel):
    site_name: List[str]
    search_term: str
    location: str
    results_wanted: int
    hours_old: int
