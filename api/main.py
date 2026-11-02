from fastapi import FastAPI, HTTPException, Depends
from routes import jobs
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Job Tracker API")
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)