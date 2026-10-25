# CREDITLENS CODE AUDIT — WHAT TO FIX BEFORE AN INTERVIEW OR PUBLIC DEMO

**Scope:** Public source-code inspection as at 25 Oct 2026. Files not run locally; priority tags reflect observed code risks, not results of executing every path.

## PRIORITY 0 — Metrics and claims you should correct first

### A01 — SQL previous-month rollover can be mathematically wrong

**Where:** `sql/03_kpi_views.sql`, `v_total_industry_monthly` and `v_sector_monthly_kpis`.  
**Code pattern:** `date(d.calendar_date, '-1 month')` with `strftime('%Y-%m', ...)`.  
**Why:** SQLite normalizes invalid month/day combinations by rolling forward. March 31 minus one month can produce March 3 rather than February.  
**Fix:** Calculate previous key from start-of-month: `strftime('%Y-%m', date(d.calendar_date, 'start of month','-1 month'))`. For prior year, normalize month-first as well.  
**Verification:** Run `03_SQL_PRACTICE.sql` Q12–Q14 and compare every period against a pandas `Period('M')` lookup. Add regression tests for Jan/Mar/May 31 and leap years.

### A02 — Historical concentration chart uses invented intermediate values

**Where:** `static/index.html`, `loadConcentrationCharts()`.  
**Observation:** `dummyMonths`, `dummyHhi`, `dummyTop3` arrays are hard-coded in the chart builder.  
**Why:** Users may interpret these illustrative values as computed monthly observations.  
**Fix:** Add `/api/credit/concentration` reading `v_industry_concentration_hhi` with `ORDER BY reporting_month ASC`; call it from JS; check 90 points.  
**Verification:** The plot's first, middle and final HHI match SQL query values exactly, not just the documented endpoint.

### A03 — Excel reconciliation not independent

**Where:** `excel/generate_reconciliation_excel.py`.  
**Observation:** Both "Python YoY" and "SQL YoY" workbook columns are populated from the **same SQL view result**. The column labeled "Excel YoY Formula" writes a precomputed Python number rather than an actual Excel formula. Status is written as a literal `MATCH`.  
**Why:** A bug in SQL could appear "reconciled" without being independently caught.  
**Fix:** Compute a separate pandas result from cleaned raw data, query SQL results independently, write true Excel formulas for sample rows, and populate status from real comparison of calculated values.  
**Verification:** Inject a controlled wrong SQL value and confirm the check flags mismatch.

### A04 — Internal HHI historical values disagree across reports

**Where:** `reports/eda_report.md` versus `README.md` / `reports/business_findings.md`.  
**Observed conflict:** EDA report says Jan 2019 **HHI 1,858.9 / Top-3 55.94%**. README/business findings say **HHI 1,713.93 / Top-3 56.84%**.  
**Why:** Historical trend conclusions depend on the correct starting value.  
**Fix:** Run independent SQL + pandas checks on raw/clean data, compare month 2019-01, update all reports, screenshots and captions from a single generated metrics file.  
**Verification:** No stale number remains in markdown/html/chart exports.

## PRIORITY 1 — Reproducibility and quality

### A05 — Raw source provenance is not fully demonstrated

**Where:** `src/ingest.py`, metadata and source URLs.  
**Observation:** Reads either hard-coded local Antigravity scratch files or bundled raw JSON. Does not make a current RBI network download; SHA-256 protects byte identity only.  
**Fix:** Remove machine-specific default paths; add optional download/import adapter, source URL + retrieval timestamp, original response filename and a published source reconciliation record. Preserve archived raw bytes rather than rewriting if byte-level provenance matters.

### A06 — Critical validation failures do not block downstream steps

**Where:** `src/pipeline.py`, `src/validate.py`.  
**Observation:** The runner calls `run_validation` and prints passed count, then continues even when the report might contain `FAIL`.  
**Fix:** Fail fast if any CRITICAL/HIGH condition invalidates key input used for the KPI layer; route records to quarantine, surface readable error summary, and leave previous good build intact.

### A07 — Incomplete monthly panel test

**Where:** `src/validate.py`.  
**Observation:** Time continuity checks existence of each month in dataset overall. A sector may be missing for a month while all months are represented by other sectors.  
**Fix:** Cross-join expected sectors × calendar months and compare to data; flag absent keys.

### A08 — Actual SQLite vs claimed PostgreSQL compatibility

**Where:** `src/load.py`, `sql/03_kpi_views.sql`, requirements and README.  
**Observation:** Loader uses `sqlite3`, and the view uses SQLite date functions. No established actual PostgreSQL migration/test path.  
**Fix:** Either describe this as a SQLite project or implement dialect-specific SQL, SQLAlchemy engine/migrations and integration tests against PostgreSQL. Don't claim dual-backend functionality untested.

### A09 — Broader Table 15 data not integrated in primary SQL fact

**Where:** `src/load.py`.  
**Observation:** Table 15 is archived/cleaned/validated, but SQL fact load uses `credit_clean.csv` from Table 16.  
**Fix:** Add separate fact model and correct category universe for Table 15; do not blindly mix amount totals across the two overlapping views.

### A10 — "DBIE Connected" user interface badge misleading

**Where:** `static/index.html`.  
**Observation:** Browser uses its own local FastAPI service. The ingest source does not prove a live RBI DBIE connection.  
**Fix:** Change to "Local analytics data available" or display last archive/update date from `/api/metadata`.

## PRIORITY 2 — Improve delivery and product polish

### A11 — Power BI is documented, not verified as a full report file

**Where:** `powerbi/dax_measures.md`, `dashboard_design.md`, `model_schema.json`.  
**Observation:** A PBIX artifact was not visible in repository inventory.  
**Fix:** Build and check a real `.pbix`: import validated fact/dim tables, define relationships and DAX, add pages/slicers, compare outputs to an independent source, save and upload screenshots.

### A12 — DAX headline total can double-count unless context guards apply

**Where:** `powerbi/dax_measures.md`.  
**Observation:** Basic `SUM(FactCredit[CreditOutstandingCr])` over a hierarchy-containing fact can include parent+child totals.  
**Fix:** Set explicit Level-1/grand-total measures and enforce appropriate hierarchy filter for every report visual.

### A13 — Schema rebuild is destructive

**Where:** `sql/01_schema.sql`; run loader calls this SQL.  
**Observation:** Drops old views and tables before re-creation.  
**Fix:** For actual production use: backups, staging-build + atomic swap, migration versioning and error rollback. Acceptable for local demonstration if documented.

### A14 — Testing count documentation disagrees with source

**Where:** README versus `tests/test_*.py`.  
**Observation:** README says 20 tests; inspection finds 21 function definitions in the four main test files (5+4+5+7).  
**Fix:** Run `python -m pytest --collect-only -q`, fix reported number, record execution results/versions.

### A15 — Improve API consistency and frontend error handling

**Where:** `src/api.py`, `static/index.html`.  
**Fix:** Validate month regex and availability; return consistent errors for unknown periods; close SQLite connections with context handling; provide loading/empty/error UI; add a concentration-series endpoint; avoid null `.toFixed()` failures on missing share.

## ROADMAP — FIVE INCREMENTAL PULL REQUESTS

| PR | Scope | Definition of done |
|---|---|---|
| PR 1 | Fix time comparisons and canonical metrics | All month-end regression tests pass; pandas and SQL agree |
| PR 2 | Real HHI API + browser charts | 90 observed months, no dummy arrays, live plot SQL comparison |
| PR 3 | Independent audit | Excel formulas, separate Python source, mismatch flagging |
| PR 4 | Robust ingestion/QA | No local scratch dependencies, source audit, quality gates, panel completeness |
| PR 5 | BI reporting and documentation | Real PBIX, verified screenshots, reconciled findings, accurate README |

## SAFE RESUME POSITIONING UNTIL FIXES ARE COMPLETE

Use language proportional to what you personally implemented/demonstrated. For instance: "Analyzed and improved an RBI-based banking credit analytics pipeline using pandas and SQL, emphasizing hierarchy-aware ETL, time-series KPIs, and data-quality checks." Do not claim deployed PostgreSQL, automated RBI refresh, live HHI history, borrower default prediction, or independently reconciled Power BI if unsupported.

## SOURCE POINTERS

- https://github.com/Hiren1604/DA-Project/blob/main/sql/03_kpi_views.sql
- https://github.com/Hiren1604/DA-Project/blob/main/static/index.html
- https://github.com/Hiren1604/DA-Project/blob/main/excel/generate_reconciliation_excel.py
- https://github.com/Hiren1604/DA-Project/blob/main/reports/eda_report.md
- https://github.com/Hiren1604/DA-Project/blob/main/reports/business_findings.md
- https://github.com/Hiren1604/DA-Project/blob/main/src/ingest.py
- https://github.com/Hiren1604/DA-Project/blob/main/src/pipeline.py
- https://github.com/Hiren1604/DA-Project/blob/main/src/load.py
