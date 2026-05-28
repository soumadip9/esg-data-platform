# Data Model — Breathe ESG Ingestion Platform

## Design Philosophy

The hard problem in ESG data is not computing carbon factors — it is reconciling heterogeneous source data into a single auditable truth. The model therefore optimizes for:

1. **Source fidelity** — every normalized row traces back to a specific ingestion run and raw payload
2. **Tenant isolation** — enterprise clients never see each other's data
3. **Review workflow** — analysts approve before auditors lock
4. **Audit replay** — immutable logs of every state change

## Entity Relationship

```
Tenant
  ├── User (analyst/admin)
  ├── PlantCode (SAP lookup)
  ├── IngestionRun
  │     ├── IngestionError (row-level failures)
  │     └── ActivityRecord (normalized rows)
  │           └── AuditLog
  └── AuditLog (ingestion-level events)
```

## Core Models

### Tenant

Organization boundary. Every query is scoped by `tenant_id` via middleware (`TenantMiddleware`) that reads the authenticated user's tenant and sets thread-local context. This is row-level multi-tenancy — simpler than schema-per-tenant, sufficient for a prototype and common in B2B SaaS at early scale.

### ActivityRecord

The normalized unit of emissions-relevant activity. One row = one auditable fact.

| Field Group | Purpose |
|-------------|---------|
| `source_type`, `ingestion_run`, `source_row_hash`, `source_reference` | Source-of-truth tracking. Hash enables deduplication on re-upload. Reference holds PO number, meter ID, or expense ID. |
| `scope`, `category` | GHG Protocol categorization. Scope 1 (direct fuel), Scope 2 (purchased electricity), Scope 3 (procurement, travel). |
| `quantity`, `unit`, `original_quantity`, `original_unit` | Unit normalization with provenance. Analysts can see what the source said vs. what we stored. |
| `activity_date`, `period_start`, `period_end` | Temporal alignment. Utility bills use billing periods; SAP uses document date. |
| `status`, `flag_reason`, `reviewed_by`, `reviewed_at` | Analyst workflow state machine. |
| `raw_payload` | JSON snapshot of parsed source row for audit replay. |
| `is_edited` | Flag when analyst corrected a value post-ingestion. |

**Status state machine:**

```
pending ──▶ approved ──▶ locked
   │            ▲
   └──▶ flagged ┘
```

Locked records are immutable. Edits are blocked at the API layer.

### IngestionRun

Tracks each file upload: counts (success/failed/flagged/duplicate), timing, uploader. Gives analysts visibility into "what came in" vs. "what failed."

### AuditLog

Append-only log. Actions: `created`, `updated`, `flagged`, `approved`, `locked`, `edited`. Stores actor, timestamp, and JSON details (old/new values for edits). Never deleted.

### PlantCode

Lookup table for SAP `WERKS` plant codes. Real SAP exports use opaque codes; without this table, site attribution is meaningless.

## Scope & Category Mapping

| Source | Typical Scope | Category |
|--------|--------------|----------|
| SAP fuel (MATKL 0101/0102) | Scope 1 | `fuel` |
| SAP procurement (other) | Scope 3 | `procurement` |
| Utility electricity | Scope 2 | `electricity` |
| Travel — flights | Scope 3 | `travel_air` |
| Travel — hotels | Scope 3 | `travel_hotel` |
| Travel — ground | Scope 3 | `travel_ground` |

## Unit Normalization

Canonical units per category:

| Category | Canonical Unit |
|----------|---------------|
| fuel | L (liters) |
| procurement | kg |
| electricity | kWh |
| travel_air / travel_ground | km |
| travel_hotel | nights |

Conversion table in `ingestion/services/units.py`. Unknown units are stored as-is and auto-flagged for analyst review.

## Deduplication

`UniqueConstraint(tenant, source_type, source_row_hash)` prevents duplicate ingestion of identical source rows. Re-uploads increment `rows_duplicate` on the ingestion run rather than creating duplicate activity records.

## Indexes

- `(tenant, status)` — review queue queries
- `(tenant, source_type)` — source-filtered views
- `(tenant, scope)` — scope reporting
- `(tenant, activity_date)` — temporal sorting

## What We Deliberately Did Not Model

- **Emission factor tables** — we store `emission_factor_ref` as a string placeholder; factor lookup is a separate domain
- **Organizational hierarchy** — cost centers are captured as `site_code` but not modeled as a tree
- **Currency / spend-based emissions** — we normalize physical units, not financial spend

See [TRADEOFFS.md](./TRADEOFFS.md) for more.
