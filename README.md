# Breathe ESG — Emissions Data Ingestion & Review Platform

**App** : https://breathe-esg-web-ui0n.onrender.com 

A Django REST + React prototype for ingesting heterogeneous emissions **activity data** from enterprise clients, normalizing it into a single auditable format, and giving analysts a review workflow before data is locked for external auditors.

Built for the **Breathe ESG Tech Intern Assignment**.

---

## Live Demo

| | URL |
|---|-----|
| **API** | https://breathe-esg-api-v0ko.onrender.com |
| **Health check** | https://breathe-esg-api-v0ko.onrender.com/health/ |
| **GitHub** | https://github.com/soumadip9/esg-data-platform |

> Free-tier services spin down after ~15 min idle. First load may take 30–60 seconds.

---

## Login Credentials

| Username | Password | Tenant | Data |
|----------|----------|--------|------|
| `analyst` | `demo1234` | Acme Corporation | ~29 sample records (auto-loaded on deploy) |
| `analyst2` | `demo1234` | Globex Industries | Empty by default — upload your own files to test isolation |
| `admin` | `admin1234` | Acme Corporation | Django admin (local / server only) |

---

## What This App Does (Simple Explanation)

Companies report carbon emissions using data from many different systems in many different formats. This app:

1. **Ingests** files from 3 source types (SAP, utility portals, corporate travel)
2. **Normalizes** quantities, units, and dates into one standard format
3. **Classifies** each row by GHG Scope (1 / 2 / 3)
4. **Flags** suspicious rows automatically (unknown units, outliers, estimated reads)
5. **Lets analysts review**, edit, approve, and lock rows before audit

**Important:** This app ingests **activity data** (liters of fuel, kWh of electricity, km of travel) — it does **not** calculate CO₂. That is a deliberate design choice documented in [TRADEOFFS.md](./TRADEOFFS.md).

---

## Problem Context (Assignment)

A PM scenario: a new enterprise client has:

- **SAP** — fuel and procurement data
- **Utility portals** — electricity billing data
- **Corporate travel platform** — flights, hotels, ground transport

The hard part is not computing carbon — it is reconciling messy, inconsistent source data and giving analysts confidence before auditors sign off.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   React UI      │────▶│   Django REST    │────▶│   PostgreSQL    │
│   (Vite/TS)     │     │   API            │     │   (multi-tenant)│
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                        ┌────────▼─────────┐
                        │  Celery + Redis  │  (async ingestion;
                        │  eager on Render │   sync in production config)
                        └──────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 5, Django REST Framework, SimpleJWT |
| Frontend | React 18, TypeScript, Vite |
| Database | PostgreSQL (production), SQLite (local dev) |
| Task queue | Celery + Redis |
| Deployment | Docker, Render |
| Static files | WhiteNoise (API), Nginx (frontend container) |

### Project Structure

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
├── MODEL.md               # Data model rationale
├── DECISIONS.md           # Format & design decisions
├── TRADEOFFS.md           # What we deliberately did not build
├── SOURCES.md             # Research & sample data design
├── DEPLOY.md              # Render deployment guide
├── docker-compose.yml
└── render.yaml
```

---

## Features

### Data Ingestion (3 Sources)

| Source | File format | Parser | Ingestion method |
|--------|-------------|--------|------------------|
| SAP procurement & fuel | Tab-delimited TSV (ME80FN export) | `parsers/sap.py` | File upload |
| Utility electricity | CSV (Green Button style) | `parsers/utility.py` | File upload |
| Corporate travel | Pipe-delimited (`\|`) Concur SAE subset | `parsers/travel.py` | File upload |

Each parser:
- Handles real-world quirks (German SAP headers, billing period misalignment, missing flight distances)
- Normalizes units (GAL→L, mi→km, MWh→kWh)
- Assigns Scope 1 / 2 / 3
- Auto-flags suspicious rows instead of silently dropping them
- Deduplicates by SHA-256 hash of source row

### Review Dashboard

- Total / pending / flagged / approved / locked counts
- Breakdown by data source and GHG scope
- Action-required prompt when flagged rows exist

### Review Queue

- Filter by status and source type
- Bulk **Approve**, **Flag**, **Lock approved**
- **History** panel — full audit trail per row (who did what, when)
- **Edit** modal — analysts can correct quantity, unit, description, site, notes
- **Edited** badge on corrected rows
- Locked rows cannot be edited

### Ingestion Page

- Upload files by source type
- Recent ingestion runs table: success / failed / flagged / duplicate counts

### Multi-Tenancy

- Row-level isolation via `Tenant` FK on every record
- `TenantMiddleware` + `TenantQuerysetMixin` enforce scoping on all API queries
- Two demo tenants seeded: **Acme Corporation** and **Globex Industries**
- Analysts at one tenant never see another tenant's data

### Audit Trail

- Immutable `AuditLog` model
- Logs: created, approved, flagged, locked, edited
- Stores actor, timestamp, and JSON details (old/new values on edits)
- Visible in UI via History panel + available at API

---

## Data Flow

```
sample_data/*.tsv|csv|txt
        │
        ▼
  File upload  OR  load_samples (on deploy)
        │
        ▼
  Parser (SAP / Utility / Travel)
        │
        ▼
  Normalize units + assign Scope 1/2/3
        │
        ▼
  Flag suspicious rows (if any)
        │
        ▼
  PostgreSQL → ActivityRecord
        │
        ▼
  Django REST API
        │
        ▼
  React Dashboard / Review Queue
        │
        ▼
  Analyst approves → locks for audit
```

---

## Sample Data

Files in `sample_data/` are hand-crafted to mimic real export formats. See [SOURCES.md](./SOURCES.md) for research rationale.

| File | Upload as | Expected result |
|------|-----------|-----------------|
| `sap_procurement.tsv` | SAP Procurement (TSV) | ~11 rows, ~3 flagged (outlier diesel, GAL conversion, unknown unit) |
| `utility_electricity.csv` | Utility Electricity (CSV) | ~8 rows, ~1 flagged (estimated meter read) |
| `travel_expense.txt` | Corporate Travel | ~8–10 rows, some with distance estimation flags |

### Upload tips

- **SAP must be `.tsv` (tab-separated)** — do not upload `.csv` for SAP
- **Do not open CSV in Excel before upload** — Excel changes dates and separators
- **Re-uploading the same file** shows as **Duplicates**, not new Success rows

---

## GHG Scope Classification

| Data | Scope | Category |
|------|-------|----------|
| Diesel, fuel, heating oil | Scope 1 | `fuel` |
| Purchased electricity | Scope 2 | `electricity` |
| Procurement (materials, equipment) | Scope 3 | `procurement` |
| Business flights | Scope 3 | `travel_air` |
| Hotels | Scope 3 | `travel_hotel` |
| Ground transport | Scope 3 | `travel_ground` |

---

## Review Workflow (State Machine)

```
pending ──▶ approved ──▶ locked
   │            ▲
   └──▶ flagged ┘
```

| Status | Meaning |
|--------|---------|
| Pending | Parsed successfully, awaiting analyst review |
| Flagged | Auto-flagged or manually flagged — needs attention |
| Approved | Analyst signed off |
| Locked | Immutable — ready for external audit |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/token/` | JWT login |
| POST | `/api/auth/token/refresh/` | Refresh JWT |
| GET | `/api/me/` | Current user + tenant |
| GET | `/api/review/dashboard/` | Dashboard stats |
| GET | `/api/activities/` | List activities (filter by status, source, scope) |
| GET | `/api/activities/{id}/` | Activity detail |
| GET | `/api/activities/{id}/audit/` | Audit log for one activity |
| POST | `/api/review/bulk/` | Bulk approve / flag / lock |
| PATCH | `/api/review/activities/{id}/edit/` | Analyst edit (blocked if locked) |
| POST | `/api/ingestion/upload/` | Upload source file |
| GET | `/api/ingestion/runs/` | List ingestion runs |
| GET | `/api/ingestion/runs/{id}/errors/` | Row-level parse errors |
| GET | `/health/` | Health check |

---

## Local Development

### Option A — Docker (recommended)

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000/api/ |
| Login | `analyst` / `demo1234` |

### Option B — Manual setup

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
set CELERY_TASK_ALWAYS_EAGER=true
python manage.py migrate
python manage.py seed_demo
python manage.py load_samples   # optional: load sample files
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

## Deployment (Render)

See [DEPLOY.md](./DEPLOY.md) for full instructions.

**Quick steps:**

1. Push repo to GitHub
2. Render → **New Blueprint** → select `esg-data-platform`
3. Apply `render.yaml` (creates DB + API + frontend)
4. Wait ~10–15 min for first deploy

**On every API deploy**, `entrypoint.sh` automatically runs:

```bash
python manage.py migrate
python manage.py seed_demo        # creates both tenants + users
python manage.py load_samples     # loads sample_data into Acme tenant
gunicorn ...
```

**Manual redeploy** (if auto-deploy didn't trigger):

Render dashboard → service → **Manual Deploy** → **Deploy latest commit**

---

## Verification Checklist

Use this to confirm everything works before submission.

### Login & tenancy
- [ ] `analyst` / `demo1234` → Acme Corporation, ~29 records on dashboard
- [ ] `analyst2` / `demo1234` → Globex Industries, 0 records (until you upload)
- [ ] Globex upload does not appear in Acme tenant

### Dashboard
- [ ] Total records > 0 for Acme
- [ ] By source shows SAP, Utility, Travel counts
- [ ] By scope shows Scope 1, 2, 3 counts

### Review Queue
- [ ] Filter **Flagged** shows rows with flag reasons
- [ ] **History** button opens audit trail panel
- [ ] **Edit** button opens modal, save creates **Edited** badge
- [ ] Bulk **Approve** changes status
- [ ] **Lock approved** locks approved rows

### Ingestion
- [ ] Upload `sap_procurement.tsv` as SAP → Completed, Success > 0
- [ ] Re-upload same file → Duplicates increase, not double-counted
- [ ] Wrong format (SAP as `.csv`) → Failed

---

## What We Deliberately Did NOT Build

Documented fully in [TRADEOFFS.md](./TRADEOFFS.md):

1. **CO₂ calculation engine** — activity data only; factor lookup is downstream
2. **Live API integrations** (SAP OData, Concur API, utility OAuth) — file upload instead
3. **Dual approval workflow** — single analyst approve → lock is sufficient for prototype

---

## Documentation (Assignment Deliverables)

| File | Purpose |
|------|---------|
| [MODEL.md](./MODEL.md) | Data model, multi-tenancy, scope mapping, audit trail, unit normalization |
| [DECISIONS.md](./DECISIONS.md) | Why TSV for SAP, CSV for utility, pipe-delimited for travel; what we ignored |
| [TRADEOFFS.md](./TRADEOFFS.md) | Three things not built and why |
| [SOURCES.md](./SOURCES.md) | Real-world format research, sample data design, production failure modes |
| [DEPLOY.md](./DEPLOY.md) | Render deployment steps and troubleshooting |

---

## Submission

**Email to Breathe ESG with:**

```
GitHub:   https://github.com/soumadip9/esg-data-platform
Live app: https://breathe-esg-web-ui0n.onrender.com
Login:    analyst / demo1234  (Acme — has sample data)
          analyst2 / demo1234 (Globex — tenant isolation demo)


## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Failed to fetch" on login | Wait 30–60s (cold start); hard refresh Ctrl+Shift+R |
| Upload shows all Failed | Wrong file format — SAP needs `.tsv`, not `.csv` |
| Upload shows Duplicates only | Same file already ingested — expected behavior |
| analyst2 login fails | Backend not redeployed — Manual Deploy on `breathe-esg-api` |
| No History/Edit buttons | Frontend not redeployed — Manual Deploy on `breathe-esg-web`, hard refresh |
| Excel-edited CSV fails | Use original file from `sample_data/` without opening in Excel |



## License

Prototype built for the Breathe ESG Tech Intern Assignment.
