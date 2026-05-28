# Decisions — Ambiguities Resolved

## Source Format Choices

### 1. SAP — Tab-delimited flat file (ME80FN export)

**Options considered:** IDoc, OData API, BAPI, flat file export

**Chose:** Tab-delimited flat file from transaction ME80FN (General Reports on purchasing documents)

**Why:**
- Most common self-service export path for sustainability teams without IT involvement
- OData/BAPI require SAP Basis setup and RFC credentials — unrealistic for a 4-day prototype
- IDoc is batch-oriented and requires PI/PO middleware
- Flat files match what we hear from clients: "the procurement team emails us a spreadsheet monthly"

**Subset handled:**
- EKKO/EKPO header + item fields: PO number, item, document date, material, material group, plant, quantity, unit
- German column header aliases (WERK, BELEGDATUM, EINHEIT) for EU deployments
- Fuel classification via material group (0101, 0102) and keyword matching

**Ignored:**
- Account assignment (EKKN table)
- Schedule lines, goods receipt, invoice matching
- Service POs with no material number
- Multi-currency conversion

**Would ask PM:** "Do they export from ME80FN or do they have a BW/DataSource extractor? Is there a material master we can sync for fuel classification?"

### 2. Utility — Portal CSV export (Green Button style)

**Options considered:** PDF bill OCR, utility API, AMI interval data, consolidated billing spreadsheet

**Chose:** CSV portal export modeled on Green Button "Download My Data"

**Why:**
- Facilities teams most commonly download CSV from utility portals monthly
- PDF OCR is fragile, expensive, and error-prone — wrong tool for a prototype
- AMI interval data (15-min reads) is overkill for monthly GHG reporting and creates massive files
- Consolidated billing is the enterprise path but requires utility partnership

**Subset handled:**
- Monthly billing period usage in kWh
- Meter ID, account number, facility name, period start/end
- Estimated vs. actual read flagging
- Non-electricity rows skipped

**Ignored:**
- Time-of-use tariff breakdown
- Solar export / net metering (negative usage flagged but not excluded)
- Multi-meter "Multiple" aggregation from Green Button spec
- Demand charges (kW)

**Would ask PM:** "Which utility providers? Do they have Green Button or a custom portal? Do billing periods align to calendar months or stagger?"

### 3. Corporate Travel — Pipe-delimited SAE subset

**Options considered:** Concur API, Navan API, manual Excel export, full SAE v3 (400 columns)

**Chose:** Pipe-delimited file mimicking Concur Standard Accounting Extract (SAE) entry-level fields

**Why:**
- SAE is the standard finance integration format — well-documented, pipe-delimited
- Full API access requires Concur professional services engagement
- Excel export lacks airport codes and distance — SAE entry-level has location fields
- A subset of ~15 columns covers flights, hotels, and ground transport

**Subset handled:**
- Expense type classification (airfare, hotel, car rental, rail, taxi)
- Airport codes with distance estimation lookup table for common routes
- Mileage conversion (mi → km)
- Hotel nights from quantity field

**Ignored:**
- VAT/tax itemization (doubles rows in real SAE)
- Allocations across cost centers
- Per-diems and meals
- Rail vs. air multi-leg itineraries

**Would ask PM:** "Concur or Navan? Do they have SAE configured or just Excel exports? Are airport codes captured as custom fields?"

## Ingestion Mechanism

**Chose:** File upload via REST API (multipart form)

**Why:** Matches how data actually arrives — emailed attachments, portal downloads, shared drives. API pull would require stored credentials and scheduling infrastructure we can't demo in 4 days.

**Production path:** Same parsers, triggered by S3 drop, SFTP poll, or email attachment processor.

## Multi-Tenancy

**Chose:** Shared database, row-level tenant scoping via FK + middleware

**Why:** Simplest correct approach for a prototype. Schema-per-tenant adds migration complexity; database-per-tenant adds ops overhead. Row-level is what most early-stage B2B SaaS uses.

## Authentication

**Chose:** JWT (SimpleJWT) with username/password

**Why:** Stateless, works with React SPA, standard for DRF. No SSO/OAuth complexity needed for prototype.

## Async Processing

**Chose:** Celery + Redis, with `CELERY_TASK_ALWAYS_EAGER=true` for dev/single-container deploy

**Why:** File parsing can be slow on large exports. Celery is production-standard. Eager mode lets us deploy to Render free tier without a separate worker process.

## Flagging vs. Rejecting

**Chose:** Auto-flag suspicious rows, never silently drop valid-parse rows

**Why:** Analysts need to see everything. A row with an unknown unit or estimated meter read should appear flagged, not disappear. Only parse failures go to `IngestionError`.

## Frontend Framework

**Chose:** React + Vite + TypeScript (no component library)

**Why:** Assignment specifies React. Custom CSS keeps bundle small and demonstrates UX judgment without hiding behind Material UI defaults.

## Deployment

**Chose:** Render with Docker, PostgreSQL managed database

**Why:** Free tier, Docker support, blueprint via `render.yaml`. Railway/Fly are equally valid.

## Questions I Would Ask the PM

1. How many legal entities / plants does this client have? Do we need entity-level reporting?
2. What reporting period — calendar year, fiscal year, or rolling 12 months?
3. Is there an existing material master or fuel type mapping from SAP we should import?
4. Who signs off — one analyst or dual approval before audit lock?
5. Do auditors need the raw source files retained, or just the normalized data + audit log?
6. What's the re-upload policy — replace, append, or merge?
