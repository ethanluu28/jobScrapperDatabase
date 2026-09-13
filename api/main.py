from fastapi import FastAPI, HTTPException, Depends
from routes import jobs

app = FastAPI(title="Job Tracker API")
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])