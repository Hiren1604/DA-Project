# CreditLens — Data Dictionary

## 1. Overview
This data dictionary documents all entities, fields, data types, and hierarchy semantics across the raw ingestion files, cleaned fact tables, dimension tables, and derived analytical views in the CreditLens system.

---

## 2. Table: `fact_credit_outstanding`
Central relational fact table capturing monthly banking credit deployment.
- **Grain:** One record per sector per reporting period.
- **Total Records:** 3,870 observations (Jan 2019 – Jun 2026).

| Column Name | Data Type | Nullable | Primary/Foreign Key | Description | Permissible Values / Format |
|---|---|---|---|---|---|
| `observation_id` | INTEGER | No | PK | Unique surrogate key for each credit observation | `1, 2, 3, ...` |
| `date_id` | INTEGER | No | FK -> `dim_date.date_id` | Foreign key referencing the reporting date | References `dim_date` |
| `sector_id` | INTEGER | No | FK -> `dim_sector.sector_id` | Foreign key referencing the industry sector | References `dim_sector` |
| `source_id` | INTEGER | No | FK -> `dim_source.source_id` | Foreign key referencing the publishing source | References `dim_source` |
| `credit_outstanding_cr` | NUMERIC(15, 2) | No | None | Total outstanding bank credit in Rupees crore | Non-negative decimal (e.g. `1511787.18`) |
| `quality_status` | VARCHAR(20) | No | None | Validation status flag | `'valid'`, `'review'` |

---

## 3. Table: `dim_sector`
Taxonomy and hierarchy dimension representing Indian industries and sub-sectors as classified by the RBI.

| Column Name | Data Type | Nullable | Primary/Foreign Key | Description | Permissible Values / Examples |
|---|---|---|---|---|---|
| `sector_id` | INTEGER | No | PK | Unique surrogate key for the sector | `1, 2, ... 43` |
| `sector_code` | VARCHAR(32) | No | Unique Key | RBI official hierarchical classification code | `'2'`, `'2.1'`, `'2.18'`, `'2.18.1'` |
| `sector_name` | VARCHAR(255) | No | None | Standardized, cleaned industry title | e.g. `'Infrastructure'`, `'Basic Metal & Metal Product'` |
| `parent_code` | VARCHAR(32) | Yes | None | Immediate parent code in the RBI hierarchy | `''` (for top levels) or e.g. `'2'`, `'2.18'` |
| `parent_sector_name` | VARCHAR(255) | Yes | None | Standardized title of the immediate parent | e.g. `'Infrastructure'` for Roads |
| `hierarchy_level` | VARCHAR(32) | No | None | Categorical hierarchy tier | `'grand_total'`, `'sector_total'`, `'sub_sector'` |
| `is_parent_total` | BOOLEAN | No | None | True if sector contains nested component sub-sectors | `TRUE`, `FALSE` |
| `is_mutually_exclusive` | BOOLEAN | No | None | True strictly for the 19 Level-1 sectors that partition total credit | `TRUE` (exactly 19 sectors), `FALSE` |

---

## 4. Table: `dim_date`
Calendar dimension representing monthly reporting dates published by the Reserve Bank of India.

| Column Name | Data Type | Nullable | Primary/Foreign Key | Description | Permissible Values / Format |
|---|---|---|---|---|---|
| `date_id` | INTEGER | No | PK | Unique surrogate key for the date | `1, 2, ... 90` |
| `calendar_date` | DATE | No | Unique Key | Actual date of credit deployment reporting | `'YYYY-MM-DD'` (e.g. `'2026-06-30'`) |
| `reporting_month` | VARCHAR(7) | No | None | Reporting month string | `'YYYY-MM'` (e.g. `'2026-06'`) |
| `reporting_year` | INTEGER | No | None | Four-digit calendar year | `2019` to `2026` |
| `reporting_quarter` | VARCHAR(7) | No | None | Calendar quarter string | `'YYYY-Q1'` through `'YYYY-Q4'` |
| `month_num` | INTEGER | No | None | Numeric calendar month | `1` to `12` |
| `month_name` | VARCHAR(20) | No | None | English month title | `'January'`, `'February'`, ... |

---

## 5. Table: `dim_source`
Metadata and governance dimension for source auditability.

| Column Name | Data Type | Nullable | Primary/Foreign Key | Description |
|---|---|---|---|---|
| `source_id` | INTEGER | No | PK | Surrogate key for the data source |
| `source_name` | VARCHAR(100) | No | None | Publisher name (`Reserve Bank of India`) |
| `publication_table` | VARCHAR(100) | No | None | Official table identifier (`Table 16 - Industry-wise deployment`) |
| `source_url` | VARCHAR(500) | No | None | Official DBIE portal URL |
| `unit` | VARCHAR(50) | No | None | Reporting currency unit (`Rupees crores`) |
| `ingestion_version` | VARCHAR(20) | No | None | System pipeline version (`1.0.0`) |

---

## 6. Table: `data_quality_exceptions`
Quarantine table preserving all flagged, missing, or irregular records for review.

| Column Name | Data Type | Nullable | Primary/Foreign Key | Description |
|---|---|---|---|---|
| `exception_id` | INTEGER | No | PK | Surrogate key for exception record |
| `observation_id` | INTEGER | Yes | None | Reference to observation ID if applicable |
| `dataset` | VARCHAR(50) | No | None | Dataset identifier (`Industry Credit`, `Major Sectors`) |
| `rule_id` | VARCHAR(20) | No | None | Validation rule ID (`VR-01` to `VR-06`) |
| `severity` | VARCHAR(20) | No | None | Exception severity level (`CRITICAL`, `HIGH`, `MEDIUM`) |
| `error_details` | TEXT | No | None | Specific diagnostic description |
| `review_status` | VARCHAR(20) | No | None | Workflow status (`open`, `resolved`, `dismissed`) |
