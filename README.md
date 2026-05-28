# Breathe ESG — Emissions Data Ingestion & Review Platform

Django REST + React prototype for ingesting SAP procurement, utility electricity, and corporate travel data; normalizing it; and providing an analyst review dashboard before audit lock.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   React UI  │────▶│  Django REST │────▶│   PostgreSQL    │
│  (Analyst)  │     │     API      │     │  (multi-tenant) │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
                    ┌──────▼───────┐
                    │ Celery/Redis │  (async ingestion)
                    └──────────────┘
```

**Backend:** Django 5 + DRF, JWT auth, tenant-scoped queries, Celery for async file processing  
**Frontend:** React 18 + TypeScript + Vite, analyst-focused review dashboard  
**Database:** PostgreSQL (SQLite for local dev without Docker)

## Quick Start (Docker)

```bash
docker compose up --build
```

- **Frontend:** http://localhost:3000  
- **API:** http://localhost:8000/api/  
- **Login:** `analyst` / `demo1234`

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
set CELERY_TASK_ALWAYS_EAGER=true
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — API proxied to :8000

## Sample Data

Upload files from `sample_data/`:

| File | Source Type | Format |
|------|-------------|--------|
| `sap_procurement.tsv` | SAP | Tab-delimited ME80FN export |
| `utility_electricity.csv` | Utility | Green Button-style CSV |
| `travel_expense.txt` | Travel | Concur SAE pipe-delimited subset |

## Documentation

- [MODEL.md](./MODEL.md) — Data model design
- [DECISIONS.md](./DECISIONS.md) — Ambiguity resolutions
- [TRADEOFFS.md](./TRADEOFFS.md) — Deliberate omissions
- [SOURCES.md](./SOURCES.md) — Source research & sample data rationale

## Deployment

Deploy to [Render](https://render.com) using `render.yaml`:

```bash
# Push to GitHub, connect repo in Render, apply blueprint
```

Set `CORS_ALLOWED_ORIGINS` to your frontend URL and `ALLOWED_HOSTS` to your API domain.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/token/` | JWT login |
| GET | `/api/me/` | Current user |
| GET | `/api/review/dashboard/` | Dashboard stats |
| GET | `/api/activities/` | List normalized activities |
| POST | `/api/review/bulk/` | Bulk approve/flag/lock |
| POST | `/api/ingestion/upload/` | Upload source file |

## License

Prototype for Breathe ESG intern assignment.
