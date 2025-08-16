from pydantic import BaseModel, Field
from typing import List, Optional

class NoteCreate(BaseModel):
    patient_id: str = Field(..., min_length=1, max_length=128)
    author_id: str = Field(..., min_length=1, max_length=256)
    text: str = Field(..., min_length=1)
    tags: Optional[List[str]] = None

class NoteOut(BaseModel):
    id: int
    patient_id: str
    author_id: str
    source_type: str
    text: str
    tags: List[str] = []
    ocr_confidence: Optional[float] = None
    file_path: Optional[str] = None
    file_mime: Optional[str] = None

    class Config:
        from_attributes = True
