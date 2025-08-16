from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.dialects.sqlite import JSON
from .database import Base

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(128), index=True, nullable=False)
    author_id = Column(String(256), index=True, nullable=False)
    source_type = Column(String(16), index=True, nullable=False)  # manual | ocr
    text = Column(Text, nullable=False)
    tags = Column(String(512), nullable=True)  # comma-separated for SQLite simplicity
    ocr_confidence = Column(Float, nullable=True)
    file_path = Column(String(1024), nullable=True)
    file_mime = Column(String(128), nullable=True)
    checksum = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
