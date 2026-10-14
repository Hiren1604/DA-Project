-- ====================================================================
-- CreditLens KPI Analytical Views
-- Standardized views implementing the 8 core credit KPIs
-- ====================================================================

-- --------------------------------------------------------------------
-- 1. Total Industry Monthly Overview View (v_total_industry_monthly)
-- Tracks aggregate industrial bank credit outstanding and expansion rates
-- --------------------------------------------------------------------
CREATE VIEW v_total_industry_monthly AS
WITH total_monthly AS (
    SELECT 
        d.date_id,
        d.calendar_date,
        d.reporting_month,
        d.reporting_year,
        d.reporting_quarter,
        f.credit_outstanding_cr AS total_credit_cr,
        -- Calendar prior month and prior year strings
        strftime('%Y-%m', date(d.calendar_date, '-1 month')) AS prev_month_target,
        strftime('%Y-%m', date(d.calendar_date, '-1 year')) AS prev_year_target
    FROM fact_credit_outstanding f
    JOIN dim_date d ON f.date_id = d.date_id
    JOIN dim_sector s ON f.sector_id = s.sector_id
    WHERE s.sector_code = '2' AND f.quality_status = 'valid'
)
SELECT 
    curr.calendar_date,
    curr.reporting_month,
    curr.reporting_year,
    curr.reporting_quarter,
    curr.total_credit_cr,
    prev_m.total_credit_cr AS prev_month_credit_cr,
    ROUND(curr.total_credit_cr - prev_m.total_credit_cr, 2) AS mom_change_cr,
    ROUND(100.0 * (curr.total_credit_cr - prev_m.total_credit_cr) / NULLIF(prev_m.total_credit_cr, 0), 2) AS mom_growth_pct,
    prev_y.total_credit_cr AS prev_year_credit_cr,
    ROUND(curr.total_credit_cr - prev_y.total_credit_cr, 2) AS yoy_change_cr,
    ROUND(100.0 * (curr.total_credit_cr - prev_y.total_credit_cr) / NULLIF(prev_y.total_credit_cr, 0), 2) AS yoy_growth_pct
FROM total_monthly curr
LEFT JOIN total_monthly prev_m ON prev_m.reporting_month = curr.prev_month_target
LEFT JOIN total_monthly prev_y ON prev_y.reporting_month = curr.prev_year_target
ORDER BY curr.reporting_month DESC;

-- --------------------------------------------------------------------
-- 2. Detailed Sector Monthly KPIs View (v_sector_monthly_kpis)
-- Calculates MoM, YoY, and portfolio allocation share per sector per month
-- --------------------------------------------------------------------
CREATE VIEW v_sector_monthly_kpis AS
WITH sector_base AS (
    SELECT 
        f.observation_id,
        d.date_id,
        d.calendar_date,
        d.reporting_month,
        d.reporting_year,
        d.reporting_quarter,
        s.sector_id,
        s.sector_code,
        s.sector_name,
        s.parent_code,
        s.parent_sector_name,
        s.hierarchy_level,
        s.is_parent_total,
        s.is_mutually_exclusive,
        f.credit_outstanding_cr,
        strftime('%Y-%m', date(d.calendar_date, '-1 month')) AS prev_month_target,
        strftime('%Y-%m', date(d.calendar_date, '-1 year')) AS prev_year_target
    FROM fact_credit_outstanding f
    JOIN dim_date d ON f.date_id = d.date_id
    JOIN dim_sector s ON f.sector_id = s.sector_id
    WHERE f.quality_status = 'valid'
),
grand_totals AS (
    SELECT reporting_month, total_credit_cr
    FROM v_total_industry_monthly
)
SELECT 
    curr.observation_id,
    curr.calendar_date,
    curr.reporting_month,
    curr.reporting_year,
    curr.reporting_quarter,
    curr.sector_code,
    curr.sector_name,
    curr.parent_code,
    curr.parent_sector_name,
    curr.hierarchy_level,
    curr.is_parent_total,
    curr.is_mutually_exclusive,
    curr.credit_outstanding_cr,
    gt.total_credit_cr AS grand_total_industry_credit_cr,
    ROUND(100.0 * curr.credit_outstanding_cr / NULLIF(gt.total_credit_cr, 0), 4) AS sector_share_pct,
    prev_m.credit_outstanding_cr AS previous_month_credit_cr,
    ROUND(curr.credit_outstanding_cr - prev_m.credit_outstanding_cr, 2) AS mom_change_cr,
    ROUND(100.0 * (curr.credit_outstanding_cr - prev_m.credit_outstanding_cr) / NULLIF(prev_m.credit_outstanding_cr, 0), 2) AS mom_growth_pct,
    prev_y.credit_outstanding_cr AS previous_year_credit_cr,
    ROUND(curr.credit_outstanding_cr - prev_y.credit_outstanding_cr, 2) AS yoy_change_cr,
    ROUND(100.0 * (curr.credit_outstanding_cr - prev_y.credit_outstanding_cr) / NULLIF(prev_y.credit_outstanding_cr, 0), 2) AS yoy_growth_pct
FROM sector_base curr
LEFT JOIN grand_totals gt ON curr.reporting_month = gt.reporting_month
LEFT JOIN sector_base prev_m ON prev_m.sector_code = curr.sector_code AND prev_m.reporting_month = curr.prev_month_target
LEFT JOIN sector_base prev_y ON prev_y.sector_code = curr.sector_code AND prev_y.reporting_month = curr.prev_year_target
ORDER BY curr.reporting_month DESC, curr.sector_code ASC;

-- --------------------------------------------------------------------
-- 3. Latest Sector Exposure Ranking View (v_top_sectors_latest)
-- Cross-sectional ranking of the 19 mutually exclusive sectors for the latest reporting month
-- --------------------------------------------------------------------
CREATE VIEW v_top_sectors_latest AS
WITH latest_month AS (
    SELECT MAX(reporting_month) AS max_month FROM dim_date
)
SELECT 
    k.reporting_month,
    k.calendar_date,
    k.sector_code,
    k.sector_name,
    k.credit_outstanding_cr,
    k.sector_share_pct,
    k.mom_growth_pct,
    k.yoy_growth_pct,
    RANK() OVER (ORDER BY k.credit_outstanding_cr DESC) AS exposure_rank
FROM v_sector_monthly_kpis k
JOIN latest_month lm ON k.reporting_month = lm.max_month
WHERE k.is_mutually_exclusive = 1
ORDER BY k.credit_outstanding_cr DESC;

-- --------------------------------------------------------------------
-- 4. Industry Concentration & HHI View (v_industry_concentration_hhi)
-- Tracks Herfindahl-Hirschman Index and Top-3 concentration share per month
-- --------------------------------------------------------------------
CREATE VIEW v_industry_concentration_hhi AS
WITH monthly_sector_shares AS (
    SELECT 
        reporting_month,
        sector_name,
        credit_outstanding_cr,
        sector_share_pct,
        RANK() OVER (PARTITION BY reporting_month ORDER BY credit_outstanding_cr DESC) AS rnk
    FROM v_sector_monthly_kpis
    WHERE is_mutually_exclusive = 1
)
SELECT 
    reporting_month,
    COUNT(*) AS total_sectors_evaluated,
    ROUND(SUM(credit_outstanding_cr), 2) AS total_industry_credit_cr,
    ROUND(SUM(POWER(sector_share_pct, 2)), 2) AS hhi_index,
    ROUND(SUM(POWER(sector_share_pct / 100.0, 2)), 4) AS hhi_fraction,
    ROUND(SUM(CASE WHEN rnk <= 3 THEN sector_share_pct ELSE 0 END), 2) AS top3_concentration_share_pct,
    MAX(CASE WHEN rnk = 1 THEN sector_name ELSE NULL END) AS largest_sector,
    ROUND(MAX(CASE WHEN rnk = 1 THEN sector_share_pct ELSE 0 END), 2) AS largest_sector_share_pct
FROM monthly_sector_shares
GROUP BY reporting_month
ORDER BY reporting_month DESC;

-- --------------------------------------------------------------------
-- 5. Data Quality Exceptions Summary View (v_data_quality_summary)
-- Audit view aggregating flagged records by dataset, rule, and severity
-- --------------------------------------------------------------------
CREATE VIEW v_data_quality_summary AS
SELECT 
    dataset,
    rule_id,
    severity,
    review_status,
    COUNT(*) AS exception_count
FROM data_quality_exceptions
GROUP BY dataset, rule_id, severity, review_status
ORDER BY exception_count DESC;
