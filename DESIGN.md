
# Design: Scalable Patient Case Notes System (with AI Scan Support)

## A. System Architecture

### Core Components
- **Web Frontend**: Simple UI for doctors to write notes and upload scans (served by FastAPI templates/API in MVP). In production, a separate SPA (React) behind NHS identity (CIS2) or hospital SSO.
- **API Backend (FastAPI)**: REST endpoints for note creation, retrieval, search; orchestration of OCR, validation, audit logging.
- **OCR/AI Service**: Pluggable provider interface (Tesseract for MVP; AWS Textract/Azure Cognitive Services for prod). Handles PDF and images; returns text plus per-block confidence.
- **Storage**:
  - **Object Storage** for raw files (S3 with SSE-KMS; in MVP, local `./data/uploads`).
  - **Relational DB** for notes & metadata (PostgreSQL/Aurora Serverless v2; MVP uses SQLite). 
  - **Search** (optional): OpenSearch/Elasticsearch for full-text search and analytics (future).
- **Event Bus** (future): SNS/SQS or Kafka for async pipelines (de-id, analytics, ICD-10/Read code mapping).
- **Observability**: CloudWatch/Prometheus/Grafana; structured logs + audit trails.
- **Access Control**: NHS identity + RBAC (doctor, consultant, nurse). Patient-level access via context service with break-glass workflow.

### Data Model (simplified)
- `Note(id, patient_id, author_id, source_type[manual|ocr], text, tags[], created_at, ocr_confidence?, file_path?, file_mime?, checksum)`
- `Audit(id, actor_id, action, resource_type, resource_id, timestamp, context)` (future: immutable log store like AWS QLDB).

### Data Flows

**Manual entry:**
1. Doctor opens patient record → types note → submits.
2. API validates, persists to DB, emits audit event.
3. Returns created note; UI refreshes list.

**Scanned upload (image/PDF):**
1. Doctor selects file; UI uploads to API (multipart) with patient & author metadata.
2. API streams to object storage (virus scan step, size/mime validation), persists file metadata.
3. OCR service extracts text (if PDF with text layer, prefer direct text). Returns text + confidence.
4. API stores note + OCR metadata, links to file object, emits audit event.
5. Response mirrors manual flow.

### Tech Stack (proposed)
- **Backend**: FastAPI (Python 3.10+), SQLAlchemy, Pydantic.
- **DB**: PostgreSQL (Aurora Serverless v2). MVP: SQLite.
- **Object Storage**: AWS S3 + SSE-KMS, S3 Object Lambda for on-the-fly redaction thumbnails.
- **OCR/AI**: Tesseract (MVP), AWS Textract / Azure Cognitive Services for handwriting + forms.
- **Infra**: AWS (EKS or ECS Fargate), ALB + WAF, CloudFront, Route53, Secrets Manager, KMS, CloudWatch.
- **CI/CD**: GitHub Actions → OIDC to AWS, multi-env deploy with Terraform (IaC). 
- **AuthN/Z**: OIDC (NHS CIS2), JWT access tokens; fine-grained RBAC via OPA/OPA-embedded (future).

---

## B. Scalability & Infrastructure

### Scaling to Millions of Notes/Month
- **Stateless API** horizontally scaled behind ALB; autoscaling by CPU/RPS/p95 latency.
- **Asynchronous OCR**: For large PDFs or heavy handwriting, place OCR jobs on SQS; workers (Fargate/EKS) scale independently. For MVP: synchronous for small files.
- **Batch/Streaming Pipelines**: Use S3 events → SQS → Lambda for lightweight extraction; Kafka for cross-hospital analytics (de-identified).
- **DB Scaling**: Aurora Serverless v2 with read replicas; write sharding by hospital or patient hash (if needed). Use partitioning on `created_at` for housekeeping.
- **Caching**: CloudFront for static, ElastiCache/Redis for recent queries and search filters.
- **File Handling**: Multi-part uploads directly to S3 using pre-signed URLs; API receives metadata only to reduce load.

### Secure Uploads & Storage
- **Client-side & in-transit**: TLS 1.2+, HSTS, CSP. 
- **At-rest**: SSE-KMS for S3, KMS-managed keys for DB (TDE) and secrets. 
- **Validation**: File type whitelist (PDF, PNG, JPG, JPEG), size limits, antivirus (ClamAV/Lambda), checksum (SHA-256), and content disarm (optional via CDR).
- **Access Controls**: Least-privilege IAM; scoped pre-signed URLs; time-bounded access. 
- **Audit**: Append-only audit logs, immutable storage (S3 Object Lock or QLDB for high-assurance).

### GDPR & Data Privacy
- **Lawful basis**: Delivery of care; DPIA documented.
- **Data minimisation**: Store only necessary data; structured metadata; configurable retention per trust.
- **Access rights**: Patient access/rectification via patient portal; staff access logged and monitored. 
- **Data subject rights**: Deletion/anonymisation workflows and auditability.
- **Data residency**: UK-based regions (e.g., AWS eu-west-2 / eu-west-1 with agreements), cross-region DR within UK where possible.
- **Breach handling**: 72-hour notification process, SIEM alerts (GuardDuty, Security Hub).

### Infra Components (AWS example)
- **Networking**: VPC with private subnets, NAT GW, VPC Endpoints for S3.
- **Compute**: ECS Fargate services for API & OCR workers.
- **Data**: S3 (versioned, SSE-KMS), Aurora Serverless v2 (Postgres), ElastiCache (optional), OpenSearch (optional).
- **Security**: WAF, Shield, Secrets Manager, KMS, IAM boundaries.
- **Ops**: CloudWatch (metrics/logs/alarms), X-Ray tracing, Terraform IaC, GitHub Actions CI/CD.
- **Monitoring**: p95 latency, OCR job durations, error rates, storage growth, audit anomalies.

---

## C. MVP-to-Prod Hardening
1. Replace SQLite with Aurora PG; add read models or OpenSearch for search.
2. Switch to pre-signed S3 direct uploads; enable antivirus & CDR.
3. Pluggable OCR with handwriting optimisation (Textract/Azure) and form extraction.
4. Full auth (OIDC), scoped RBAC, and consent contexts; break-glass workflows.
5. Add event-driven pipelines: de-identification, coding (SNOMED/ICD-10), analytics.
6. Blue/green deployments, canary for OCR model changes; end-to-end synthetic tests.
