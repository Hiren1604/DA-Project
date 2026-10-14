-- ====================================================================
-- CreditLens Relational Schema Definition
-- Compatible with PostgreSQL and SQLite
-- ====================================================================

-- Drop existing views and tables if recreating
DROP VIEW IF EXISTS v_data_quality_summary;
DROP VIEW IF EXISTS v_industry_concentration_hhi;
DROP VIEW IF EXISTS v_top_sectors_latest;
DROP VIEW IF EXISTS v_total_industry_monthly;
DROP VIEW IF EXISTS v_sector_monthly_kpis;

DROP TABLE IF EXISTS data_quality_exceptions;
DROP TABLE IF EXISTS fact_credit_outstanding;
DROP TABLE IF EXISTS dim_source;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_sector;

-- --------------------------------------------------------------------
-- 1. Sector Dimension (dim_sector)
-- Captures hierarchical industry taxonomy and double-counting prevention flags
-- --------------------------------------------------------------------
CREATE TABLE dim_sector (
    sector_id INTEGER PRIMARY KEY,
    sector_code VARCHAR(32) NOT NULL UNIQUE,
    sector_name VARCHAR(255) NOT NULL,
    parent_code VARCHAR(32),
    parent_sector_name VARCHAR(255),
    hierarchy_level VARCHAR(32) NOT NULL,     -- 'grand_total', 'sector_total', 'sub_sector'
    is_parent_total BOOLEAN NOT NULL,         -- True if parent has nested children
    is_mutually_exclusive BOOLEAN NOT NULL    -- True strictly for the 19 Level-1 sectors
);

-- --------------------------------------------------------------------
-- 2. Date Dimension (dim_date)
-- Standard continuous reporting calendar
-- --------------------------------------------------------------------
CREATE TABLE dim_date (
    date_id INTEGER PRIMARY KEY,
    calendar_date DATE NOT NULL UNIQUE,
    reporting_month VARCHAR(7) NOT NULL,      -- 'YYYY-MM'
    reporting_year INTEGER NOT NULL,
    reporting_quarter VARCHAR(7) NOT NULL,    -- 'YYYY-QN'
    month_num INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL
);

-- --------------------------------------------------------------------
-- 3. Source Dimension (dim_source)
-- Auditability, origin URL, and governance metadata
-- --------------------------------------------------------------------
CREATE TABLE dim_source (
    source_id INTEGER PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    publication_table VARCHAR(100) NOT NULL,
    source_url VARCHAR(500) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    ingestion_version VARCHAR(20) NOT NULL
);

-- --------------------------------------------------------------------
-- 4. Credit Fact Table (fact_credit_outstanding)
-- Granularity: One observation per sector per reporting period
-- --------------------------------------------------------------------
CREATE TABLE fact_credit_outstanding (
    observation_id INTEGER PRIMARY KEY,
    date_id INTEGER NOT NULL,
    sector_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    credit_outstanding_cr NUMERIC(15, 2) NOT NULL,
    quality_status VARCHAR(20) NOT NULL DEFAULT 'valid',
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id),
    FOREIGN KEY (sector_id) REFERENCES dim_sector(sector_id),
    FOREIGN KEY (source_id) REFERENCES dim_source(source_id)
);

-- Indices for analytical querying performance
CREATE INDEX idx_fact_date ON fact_credit_outstanding(date_id);
CREATE INDEX idx_fact_sector ON fact_credit_outstanding(sector_id);
CREATE INDEX idx_fact_quality ON fact_credit_outstanding(quality_status);
CREATE INDEX idx_sector_hierarchy ON dim_sector(hierarchy_level, is_mutually_exclusive);
CREATE INDEX idx_date_month ON dim_date(reporting_month);

-- --------------------------------------------------------------------
-- 5. Data Quality Exceptions Table (data_quality_exceptions)
-- Preserves quarantined or flagged observations for traceability
-- --------------------------------------------------------------------
CREATE TABLE data_quality_exceptions (
    exception_id INTEGER PRIMARY KEY,
    observation_id INTEGER,
    dataset VARCHAR(50) NOT NULL,
    rule_id VARCHAR(20) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    error_details TEXT NOT NULL,
    review_status VARCHAR(20) NOT NULL DEFAULT 'open'
);
