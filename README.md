# ESG Data Platform — Emissions Ingestion & Review

A full-stack platform for ingesting heterogeneous emissions **activity data** from enterprise systems, normalizing it into a single auditable format, and giving analysts a review workflow before records are locked for audit.

**Stack:** Django REST + React · PostgreSQL · Celery · Docker · Render

---

## Links

| | URL |
|---|-----|
| **Web app** | https://breathe-esg-web-ui0n.onrender.com |
| **API** | https://breathe-esg-api-v0ko.onrender.com |
| **Health check** | https://breathe-esg-api-v0ko.onrender.com/health/ |
| **Repository** | https://github.com/soumadip9/esg-data-platform |

> Hosted on Render free tier — services spin down after ~15 min idle. First load may take 30–60 seconds.

---

## Demo Access

| Username | Password | Tenant | Notes |
|----------|----------|--------|-------|
| `analyst` | `demo1234` | Acme Corporation | Pre-loaded sample data (~29 records) |
| `analyst2` | `demo1234` | Globex Industries | Empty tenant — upload files to test isolation |
| `admin` | `admin1234` | Acme Corporation | Django admin (local / server only) |

---

## Overview

Enterprise carbon reporting pulls data from many systems in many formats — SAP exports, utility billing CSVs, corporate travel reports. Before any emissions calculation happens, analysts need to reconcile that raw input, catch bad rows, and sign off on what auditors will see.

This platform handles that upstream work:

1. **Ingest** files from SAP, utility portals, and corporate travel systems
2. **Normalize** quantities, units, and dates into one schema
3. **Classify** each row by GHG Scope (1 / 2 / 3)
4. **Flag** suspicious rows (unknown units, outliers, estimated meter reads)
5. **Review** — analysts edit, approve, and lock rows with a full audit trail

The platform stores **activity data** (liters of fuel, kWh of electricity, km of travel). It does not compute CO₂ — that is intentionally left to a downstream emissions factor engine.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   React UI      │────▶│   Django REST    │────▶│   PostgreSQL    │
│   (Vite/TS)     │     │   API            │     │   (multi-tenant)│
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                        ┌────────▼─────────┐
                        │  Celery + Redis  │
                        └──────────────────┘
```

| Layer | Technology |
|-------|------------|
| Backend | Django 5, Django REST Framework, SimpleJWT |
| Frontend | React 18, TypeScript, Vite |
| Database | PostgreSQL (production), SQLite (local dev) |
| Task queue | Celery + Redis |
| Deployment | Docker, Render |
| Static files | WhiteNoise (API), Nginx (frontend container) |

### Project structure

```
├── backend/
│   ├── apps/
│   │   ├── tenants/       # Multi-tenant model, plant code lookups
│   │   ├── accounts/      # Custom user model (analyst/admin roles)
│   │   ├── emissions/     # ActivityRecord, AuditLog
│   │   ├── ingestion/     # Parsers, pipeline, upload API
│   │   └── review/        # Dashboard, bulk approve, edit API
│   ├── config/            # Django settings, URLs, Celery
│   └── entrypoint.sh      # migrate → seed → load samples → gunicorn
├── frontend/
│   └── src/
│       ├── pages/         # Login, Dashboard, Review, Upload
│       └── api.ts         # API client
├── sample_data/           # Realistic test files (3 sources)
├── docker-compose.yml
└── render.yaml
```

---

## How It Works

### End-to-end flow

```
Source file (.tsv / .csv / .txt)
        │
        ▼
  Upload via UI  OR  load_samples on deploy
        │
        ▼
  Celery task → Parser (SAP / Utility / Travel)
        │
        ▼
  Normalize units, dates, plant codes
  Assign GHG Scope 1 / 2 / 3
  Flag suspicious rows
  Dedupe by SHA-256 hash of source row
        │
        ▼
  PostgreSQL → ActivityRecord
        │
        ▼
  REST API → React Dashboard / Review Queue
        │
        ▼
  Analyst reviews → approves → locks for audit
```

### Data ingestion

Three source-specific parsers handle real-world export quirks:

| Source | Format | Parser | Notes |
|--------|--------|--------|-------|
| SAP procurement & fuel | Tab-delimited TSV (ME80FN export) | `backend/apps/ingestion/parsers/sap.py` | German headers, mixed units |
| Utility electricity | CSV (Green Button style) | `backend/apps/ingestion/parsers/utility.py` | Billing period alignment |
| Corporate travel | Pipe-delimited Concur SAE subset | `backend/apps/ingestion/parsers/travel.py` | Missing flight distances estimated |

Each parser:
- Normalizes units (GAL→L, mi→km, MWh→kWh)
- Maps plant codes to tenant-specific sites
- Assigns scope and category
- Auto-flags rows that need analyst attention instead of silently dropping them
- Records row-level errors in `IngestionError` for hard parse failures

### GHG scope mapping

| Data | Scope | Category |
|------|-------|----------|
| Diesel, fuel, heating oil | Scope 1 | `fuel` |
| Purchased electricity | Scope 2 | `electricity` |
| Procurement (materials, equipment) | Scope 3 | `procurement` |
| Business flights | Scope 3 | `travel_air` |
| Hotels | Scope 3 | `travel_hotel` |
| Ground transport | Scope 3 | `travel_ground` |

### Review workflow

```
pending ──▶ approved ──▶ locked
   │            ▲
   └──▶ flagged ┘
```

| Status | Meaning |
|--------|---------|
| **Pending** | Parsed successfully, awaiting review |
| **Flagged** | Auto-flagged or manually flagged — needs attention |
| **Approved** | Analyst signed off |
| **Locked** | Immutable — ready for external audit |

Analysts can bulk approve, flag, or lock rows. Individual rows can be edited (quantity, unit, description, site, notes) until locked. Every action is recorded in an immutable audit log.

### Multi-tenancy

Every record is scoped to a `Tenant` via foreign key. `TenantMiddleware` and `TenantQuerysetMixin` enforce isolation on all API queries — an analyst at one tenant never sees another tenant's data. Two demo tenants are seeded: **Acme Corporation** (with sample data) and **Globex Industries** (empty).

### Frontend pages

| Page | Purpose |
|------|---------|
| **Login** | JWT authentication, tenant shown after sign-in |
| **Dashboard** | Record counts by status, source, and scope |
| **Review Queue** | Filter, bulk actions, History panel, Edit modal |
| **Ingestion** | Upload by source type, view recent run results |

---

## API

Base URL: `https://breathe-esg-api-v0ko.onrender.com/api`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/token/` | JWT login |
| POST | `/auth/token/refresh/` | Refresh JWT |
| GET | `/me/` | Current user + tenant |
| GET | `/review/dashboard/` | Dashboard stats |
| GET | `/activities/` | List activities (filter by status, source, scope) |
| GET | `/activities/{id}/` | Activity detail |
| GET | `/activities/{id}/audit/` | Audit log for one activity |
| POST | `/review/bulk/` | Bulk approve / flag / lock |
| PATCH | `/review/activities/{id}/edit/` | Analyst edit (blocked if locked) |
| POST | `/ingestion/upload/` | Upload source file |
| GET | `/ingestion/runs/` | List ingestion runs |
| GET | `/ingestion/runs/{id}/errors/` | Row-level parse errors |
| GET | `/health/` | Health check (no `/api` prefix) |

---

## Sample Data

Files in `sample_data/` mimic real export formats:

| File | Upload as | Expected result |
|------|-----------|-----------------|
| `sap_procurement.tsv` | SAP Procurement (TSV) | ~11 rows, ~3 flagged |
| `utility_electricity.csv` | Utility Electricity (CSV) | ~8 rows, ~1 flagged |
| `travel_expense.txt` | Corporate Travel | ~8–10 rows, some distance flags |

**Upload tips:**
- SAP must be `.tsv` (tab-separated), not `.csv`
- Do not open CSV in Excel before upload — it changes dates and separators
- Re-uploading the same file counts as **Duplicates**, not new records

---

## Running Locally

### Docker (recommended)

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000/api/ |
| Login | `analyst` / `demo1234` |

### Manual setup

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
set CELERY_TASK_ALWAYS_EAGER=true
python manage.py migrate
python manage.py seed_demo
python manage.py load_samples
python manage.py runserver
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` to `:8000`.

---

## Deployment

Deployed on [Render](https://render.com) via `render.yaml` (PostgreSQL + API + frontend).

On every API deploy, `entrypoint.sh` runs migrations, seeds demo tenants/users, and loads sample data into Acme.

See [DEPLOY.md](./DEPLOY.md) for setup steps and troubleshooting.

---

## Deliverables

Everything required by the project spec is included in this repository.

### 1. Working app — deployed

| Requirement | Location |
|-------------|----------|
| Live web app (not local-only) | https://breathe-esg-web-ui0n.onrender.com |
| REST API | https://breathe-esg-api-v0ko.onrender.com |
| Source code | https://github.com/soumadip9/esg-data-platform |
| Demo login | `analyst` / `demo1234` |

**Built with Django REST + React.** The app must:

- Ingest data from **3 source types** (SAP, utility electricity, corporate travel)
- **Normalize** quantities, units, and dates into one schema
- Provide a **review dashboard** where analysts can see:
  - What came in
  - What failed
  - What looks suspicious
  - Approve rows before they are locked for audit

Sample files in `sample_data/` are based on researched real-world export formats — not toy CSVs with made-up column names.

---

### 2. [MODEL.md](./MODEL.md) — Data model

Documents the data model and **why** it is shaped this way. Covers:

- **Multi-tenancy** — row-level tenant isolation via FK + middleware
- **Scope 1 / 2 / 3** — how activity categories map to GHG scopes
- **Source-of-truth tracking** — every row links back to an `IngestionRun` and raw source hash
- **Unit normalization** — GAL→L, mi→km, MWh→kWh, and flag-on-unknown
- **Audit trail** — immutable `AuditLog` on create, approve, flag, lock, edit

---

### 3. [DECISIONS.md](./DECISIONS.md) — Design decisions

Every ambiguity resolved: what was chosen, why, and what would be asked of a PM. Per source, documents:

- Ingestion mechanism chosen (file upload) and justification
- Format chosen (SAP TSV, utility CSV, travel pipe-delimited) and why
- **Subset handled vs. ignored** — e.g. ME80FN flat export vs. IDoc/OData; Green Button CSV vs. PDF bills; Concur SAE subset vs. full API

---

### 4. [TRADEOFFS.md](./TRADEOFFS.md) — Three deliberate omissions

Three things **not built** and why:

1. **CO₂ / emission factor engine** — activity data only; calculation is downstream
2. **Live API integrations** — SAP OData, Concur API, utility OAuth; file upload demonstrates the same parsers
3. **Dual approval workflow** — single analyst approve → lock is sufficient for this prototype

---

### 5. [SOURCES.md](./SOURCES.md) — Source research

Per source (SAP, utility, travel):

- What was researched (export formats, real-world quirks)
- What was learned (German headers, billing period misalignment, airport codes without distance)
- What the sample data looks like and why
- What would break in production (Excel date corruption, unit mismatches, duplicate re-uploads)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Failed to fetch" on login | Wait 30–60s for cold start; hard refresh (Ctrl+Shift+R) |
| Upload shows all Failed | Wrong format — SAP needs `.tsv`, not `.csv` |
| Upload shows Duplicates only | Same file already ingested — expected |
| No History/Edit buttons | Frontend not redeployed — redeploy `breathe-esg-web`, hard refresh |
| Excel-edited CSV fails | Use original file from `sample_data/` without opening in Excel |
