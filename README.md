
# Scalable Patient Case Notes System (MVP)

This repository contains a working proof-of-concept for a single hospital. Doctors can:
- Upload a scanned case note (image/PDF), which is OCR'd to structured text.
- Manually type a case note.
- Retrieve and list notes via API or a simple web UI.

> **Tech stack (MVP):** FastAPI + SQLite + SQLAlchemy + Tesseract OCR (via `pytesseract`) + pdf2image (Poppler).

## Quick Start (Local)

### 1) Python (no Docker)
**Prereqs:** Python 3.10+, Tesseract OCR, Poppler (for PDF), and system libs to run `pdf2image`.

- macOS (brew):
  ```bash
  brew install tesseract poppler
  ```
- Ubuntu/Debian:
  ```bash
  sudo apt-get update && sudo apt-get install -y tesseract-ocr poppler-utils
  ```

**Install & run:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000
```
Open: http://localhost:8000

### 2) Docker (recommended, one command)
```bash
docker compose up --build
```
Open: http://localhost:8000

---

## API Overview

- `POST /notes` — Create manual note
  ```json
  {
    "patient_id": "NHS-12345",
    "author_id": "dr.smith@hospital.nhs.uk",
    "text": "Patient stable. BP 120/80. Continue meds.",
    "tags": ["rounds","bp"]
  }
  ```

- `POST /notes/upload` — Upload PDF/image; performs OCR
  - form-data: `file` (pdf/png/jpg/jpeg), `patient_id`, `author_id`, optional `tags` (comma-separated)

- `GET /notes` — List notes with filters: `patient_id`, `source_type` (`manual`|`ocr`), `q` (search text), pagination `limit`/`offset`

- `GET /notes/{id}` — Fetch a single note

Files are stored under `./data/uploads/` (configurable via env). Database is SQLite at `./data/notes.db`.

---

## Assumptions

- Authentication/SSO, RBAC, and full audit logging are out of scope for the MVP (stubbed via headers); see `SECURITY.md` in design for the planned approach.
- OCR uses Tesseract locally. In production we’d support pluggable backends (AWS Textract, Azure Cognitive Services) via the same interface.
- Basic PII handling included (minimization, encryption-at-rest via disk if using Docker bind on encrypted volume); full KMS/HSM setup is described in design doc.
- The HTML UI is intentionally minimal to demonstrate the workflow; primary interface is the API.

---

## Project Layout

```
backend/
  app.py            # FastAPI app & routes
  database.py       # DB session & init
  models.py         # SQLAlchemy models
  schemas.py        # Pydantic DTOs
  ocr.py            # OCR service (Tesseract + PDF support)
  requirements.txt
  templates/
    index.html
  static/
    style.css
Dockerfile
docker-compose.yml
DESIGN.md           # Brief system design (2–3 pages)
.env.example
```

---

## Tests (Smoke)

- Manual create:
  ```bash
  curl -X POST http://localhost:8000/notes -H "Content-Type: application/json" -d '{
    "patient_id":"NHS-1","author_id":"dr@example.nhs.uk","text":"Hello OCR-less world","tags":["manual"]
  }'
  ```

- OCR upload (image):
  ```bash
  curl -F "patient_id=NHS-1" -F "author_id=dr@example.nhs.uk" -F "file=@/path/to/sample.jpg" http://localhost:8000/notes/upload
  ```

- List:
  ```bash
  curl "http://localhost:8000/notes?patient_id=NHS-1&limit=5"
  ```

---

## License
MIT (for the sake of the exercise).
