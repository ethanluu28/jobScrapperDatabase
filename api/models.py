from sqlalchemy import Boolean, Column, Text, Integer, String, Float, TIMESTAMP
from sqlalchemy.sql import func
from database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    job_url = Column(String, nullable=False, unique=True)
    site = Column(String)
    title = Column(String)
    company = Column(String)
    location = Column(String)
    is_remote = Column(Boolean)
    job_type = Column(Text)
    min_amount = Column(Float)
    max_amount = Column(Float)
    currency = Column(Text)
    status = Column(String, server_default="New")
    date_posted = Column(String)
    date_scraped = Column(String)
    description = Column(Text)

