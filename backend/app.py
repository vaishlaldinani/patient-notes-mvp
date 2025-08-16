import os, mimetypes
from typing import List, Optional

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from .database import Base, engine, get_db, DATA_DIR
from .models import Note
from .schemas import NoteCreate, NoteOut
from .ocr import ocr_file_to_text, ALLOWED_MIME, sha256_file

UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(DATA_DIR, "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Patient Notes MVP", version="0.1.0")
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Init DB
Base.metadata.create_all(bind=engine)

# --- UI ---
@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: Optional[str] = None):
    return templates.TemplateResponse("index.html", {"request": request, "q": q or ""})

# --- API ---
@app.post("/notes", response_model=NoteOut)
def create_note(note: NoteCreate, db: Session = Depends(get_db), x_user_id: Optional[str] = None):
    # Basic stub for auth: prefer header X-User-Id if provided
    author_id = note.author_id or x_user_id
    obj = Note(
        patient_id=note.patient_id,
        author_id=author_id,
        source_type="manual",
        text=note.text,
        tags=','.join(note.tags) if note.tags else None
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return to_schema(obj)

@app.post("/notes/upload", response_model=NoteOut)
async def upload_note(
    patient_id: str = Form(...),
    author_id: str = Form(...),
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Validate mime
    mime = file.content_type
    if mime not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {mime}")

    # Save file
    safe_name = file.filename.replace('/', '_')
    dest_path = os.path.join(UPLOAD_DIR, safe_name)
    i = 1
    while os.path.exists(dest_path):
        name, ext = os.path.splitext(safe_name)
        dest_path = os.path.join(UPLOAD_DIR, f"{name}_{i}{ext}")
        i += 1

    with open(dest_path, 'wb') as out:
        content = await file.read()
        out.write(content)

    checksum = sha256_file(dest_path)

    # OCR
    try:
        text, conf = ocr_file_to_text(dest_path, mime)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")

    if not text:
        text = "[[ No text recognized ]]"

    obj = Note(
        patient_id=patient_id,
        author_id=author_id,
        source_type="ocr",
        text=text,
        tags=tags,
        ocr_confidence=conf,
        file_path=dest_path,
        file_mime=mime,
        checksum=checksum
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return to_schema(obj)

@app.get("/notes", response_model=List[NoteOut])
def list_notes(
    db: Session = Depends(get_db),
    patient_id: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None, pattern="^(manual|ocr)$"),
    q: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    stmt = select(Note)
    if patient_id:
        stmt = stmt.where(Note.patient_id == patient_id)
    if source_type:
        stmt = stmt.where(Note.source_type == source_type)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Note.text.like(like), Note.tags.like(like)))
    stmt = stmt.order_by(Note.created_at.desc()).limit(limit).offset(offset)
    rows = db.execute(stmt).scalars().all()
    return [to_schema(n) for n in rows]

@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id:int, db: Session = Depends(get_db)):
    row = db.get(Note, note_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return to_schema(row)

@app.get("/files/{note_id}")
def get_original_file(note_id:int, db: Session = Depends(get_db)):
    row = db.get(Note, note_id)
    if not row or not row.file_path or not os.path.exists(row.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(row.file_path, media_type=row.file_mime, filename=os.path.basename(row.file_path))

def to_schema(n: Note) -> dict:
    return {
        "id": n.id,
        "patient_id": n.patient_id,
        "author_id": n.author_id,
        "source_type": n.source_type,
        "text": n.text,
        "tags": [t for t in (n.tags.split(',') if n.tags else []) if t],
        "ocr_confidence": n.ocr_confidence,
        "file_path": n.file_path,
        "file_mime": n.file_mime,
    }
