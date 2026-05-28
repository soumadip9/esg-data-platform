# Sources — Research, Sample Data & Production Gaps

## 1. SAP Procurement (Fuel & Materials)

### Real-world format researched

- **SAP ME80FN** (General Reports) exports purchasing document header/item data from tables **EKKO** (header) and **EKPO** (items)
- Standard fields: `EBELN` (PO number), `EBELP` (item), `BEDAT` (document date), `MATNR` (material), `MATKL` (material group), `WERKS` (plant), `MENGE` (quantity), `MEINS` (unit)
- EU deployments often use German labels: `BELEGDATUM`, `WERK`, `EINHEIT`, `BESTELLUNG`
- Fuel-specific data may extend to industry tables like `OIRC_FUELS_PR` (temperature, density) — we don't handle these
- Export is typically tab-delimited when saved from SAP GUI spreadsheet view

**References:**
- SAP Help Portal: Purchasing Data (Item Level) DataSource documentation
- SAP Community: MM integration mapping documents

### What we learned

- Plant codes (`WERKS`) are opaque without a lookup table — we model `PlantCode`
- Material group `0101`/`0102` commonly indicates fuel/energy in many SAP charts of accounts
- Units vary: `L`, `M3`, `GAL`, `KG`, `EA` — normalization is essential
- Date formats include `YYYYMMDD`, `DD.MM.YYYY`, and ISO — parser tries all three
- Document type `NB` is standard purchase order

### Sample data: `sample_data/sap_procurement.tsv`

| Design choice | Reason |
|---------------|--------|
| Tab-delimited with English SAP field names | Most common export format from ME80FN |
| Mix of fuel (0101) and non-fuel (0205, 0301) rows | Tests scope classification logic |
| GAL unit on Chicago plant row | Tests unit conversion (GAL → L) |
| Plant codes 1000/2000/3000/UK01 | Maps to seeded `PlantCode` lookup |
| Row with 999999 L diesel | Intentional outlier to trigger analyst flagging in review |
| `EA` (each) for laptops and office supplies | Tests non-fuel procurement → Scope 3 |

### What would break in production

- **Custom Z-fields** — clients add fields via user exits; our column map won't know them
- **Multi-company code** — same PO number across mandants (clients)
- **Material numbers with leading zeros stripped** by Excel — hash dedup would fail on re-export
- **Service POs** without material numbers — we skip or misclassify
- **IDoc instead of flat file** — completely different parser needed

---

## 2. Utility Electricity

### Real-world format researched

- **Green Button "Download My Data"** — standard CSV/XML export from utility customer portals (Oracle Utilities, many US/EU providers)
- Typical columns: Meter ID, Account Number, Service Address, Start Date, End Date, Usage, Units, Type, Read Type
- Consolidated billing spreadsheets are the enterprise alternative (DOE Energy Data Guide)
- Billing periods often don't align to calendar months (e.g., Jan 15 – Feb 14)
- AMI interval data adds timestamp granularity we don't need for monthly GHG

**References:**
- Oracle Utilities Green Button documentation
- DOE Energy Data Guide Step 4: Streamline Access to Utility Data
- ENERGY STAR Portfolio Manager web services (for API-based alternative)

### What we learned

- No standardized CSV schema — column names vary by utility; we use alias mapping
- "Estimated" reads are common and should be flagged for analyst verification
- Solar export appears as negative usage — we ingest but don't exclude
- Multi-meter accounts show "Multiple" instead of meter ID in Green Button spec
- kWh is the canonical unit; MWh and GJ appear in some European exports

### Sample data: `sample_data/utility_electricity.csv`

| Design choice | Reason |
|---------------|--------|
| Green Button-style column names | Most documented portal export format |
| Billing periods mid-month (15th–14th) | Reflects real misalignment with calendar months |
| One "Estimated" read (Munich Dec-Jan) | Tests auto-flagging |
| Chicago row spanning Nov 28 – Jan 2 (35+ days) | Tests billing period span flag |
| Negative usage solar row | Tests edge case visibility (not silently dropped) |
| Multiple facilities across DE/US/GB | Multi-site enterprise client |

### What would break in production

- **PDF bills** — completely different ingestion path (OCR or manual entry)
- **Unit not in conversion table** (e.g., `ccf` for gas mislabeled as electricity)
- **Consolidated multi-utility spreadsheet** with different column layouts per sheet
- **Duplicate meter IDs** across accounts after merger/acquisition
- **Green Button XML** instead of CSV — different parser, same canonical output

---

## 3. Corporate Travel (Flights, Hotels, Ground)

### Real-world format researched

- **SAP Concur Standard Accounting Extract (SAE) v3** — pipe-delimited, up to 400 columns
- Entry-level fields include: expense type, transaction date, vendor, amount, location data
- SAE defaults to `|` delimiter; multi-file ZIP for large extracts
- Airport codes often captured as custom fields, not standard SAE columns — we simulate them
- Distance frequently missing for flights — only airport codes available
- Hotel expenses itemize room/meals in real SAE (doubles rows) — we use simplified single row

**References:**
- Concur Standard Accounting Extract v3 specification (BMS Main deployment guide)
- SAP Learning: Expense File Export basics
- SAP Community: SAE header templates

### What we learned

- Expense type string drives category classification ("Airfare" → air, "Hotel" → hotel)
- Mileage reported in miles (US) or km (EU) — normalization required
- Flight distance often absent — must estimate from airport pair or flag
- Rail, taxi, and car rental have different emission factors
- Cost center / employee ID useful for attribution but not for emissions calc

### Sample data: `sample_data/travel_expense.txt`

| Design choice | Reason |
|---------------|--------|
| Pipe-delimited (`\|`) | SAE default format |
| JFK-LHR without distance | Tests airport-pair distance estimation |
| SFO-ORD with explicit 2960 km | Tests provided distance path |
| FRA-MUC short-haul | Tests domestic factor ref selection |
| Hotel with 3 and 5 nights | Tests nights-based activity |
| Ground transport in miles | Tests mi → km conversion |
| SIN-HKG without distance | Tests missing lookup table entry → flag |
| Mix of USD/EUR/GBP amounts | Realistic multinational travel (amount stored in raw_payload, not used for calc) |

### What would break in production

- **Full SAE with VAT rows** — each expense creates 2× rows (GL + tax); dedup logic would break
- **Multi-leg flights** stored as single expense with no segment detail
- **Custom fields not in our column map** — airport codes stored differently per client
- **Navan vs. Concur** — different export schemas entirely
- **Policy-violating expenses** flagged in travel system but not in export

---

## Sample Data Loading

Upload the three files via the Ingestion page (`/upload`) selecting the matching source type. Or use Docker:

```bash
# After docker compose up and seed_demo
curl -X POST http://localhost:8000/api/ingestion/upload/ \
  -H "Authorization: Bearer <token>" \
  -F "source_type=sap" \
  -F "file=@sample_data/sap_procurement.tsv"
```

Expected results after loading all three files:
- ~11 SAP activities (1 flagged outlier, 1 GAL conversion)
- ~7 utility activities (1 estimated, 1 long period, 1 negative/solar)
- ~9 travel activities (several with distance estimation flags)
