# Tradeoffs — Three Things We Deliberately Did Not Build

## 1. Emission Factor Engine & CO₂e Calculation

**What we skipped:** A full emission factor lookup service that takes normalized activity data and computes CO₂e using DEFRA, EPA, or client-specific factors.

**Why:**
- The assignment explicitly states "the hard part isn't computing carbon" — it's ingestion and normalization
- Factor selection is politically sensitive (location-based vs. market-based Scope 2, DEFRA vs. EPA) and requires client-specific configuration
- Building a toy calculator would be "slop" — a number that looks precise but uses wrong factors

**What we did instead:** Store `emission_factor_ref` as a string placeholder and `estimated_co2e_kg` as a nullable field. The data model is ready; the calculation is a downstream service.

**Production path:** Separate microservice or Celery task that reads approved+locked records, applies tenant-configured factor sets, and writes to an `EmissionCalculation` table.

---

## 2. Real-Time API Integrations (SAP OData, Concur API, Utility Green Button Connect)

**What we skipped:** Live API pulls from source systems with OAuth, credential vaults, and scheduled sync jobs.

**Why:**
- Each integration is a multi-week project requiring client IT credentials and sandbox access
- SAP OData requires S/4HANA or BTP setup; Concur API requires professional services
- Green Button Connect My Data needs utility-specific OAuth registration
- File upload demonstrates the same parsing pipeline with realistic data shapes

**What we did instead:** File upload endpoint with production-grade parsers. The parser interface (`ParseResult` → `ParsedActivity`) is identical whether input comes from a file or an API response.

**Production path:** Add `IngestionConnector` model with credential refs, Celery beat schedules, and adapter classes that fetch data and pass it to the same parsers.

---

## 3. Dual Approval Workflow & Role-Based Permissions

**What we skipped:** Multi-stage approval (analyst review → manager sign-off → auditor lock) with granular RBAC.

**Why:**
- The assignment asks for "analysts review and sign off" — singular stage
- Dual approval rules vary by client (some need SOX-style segregation of duties, others don't)
- Over-engineering permissions before understanding the client's governance model is premature

**What we did instead:** Simple state machine (pending → flagged → approved → locked) with two roles (analyst, admin). Bulk approve/flag/lock actions. Audit log captures who did what.

**Production path:** Add `ApprovalPolicy` model per tenant (required approvers, segregation rules), workflow engine, and email notifications. The `AuditLog` already supports replay.

---

## Honorable Mentions (also not built)

- PDF utility bill OCR
- Data quality scoring / ML anomaly detection
- Versioned re-upload merge strategy
- Export to CDP/GRI report formats
- Full i18n for German SAP column headers in the UI (handled in parser only)
