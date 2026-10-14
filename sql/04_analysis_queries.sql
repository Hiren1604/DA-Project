-- ====================================================================
-- CreditLens Deep-Dive Analysis Queries
-- Answering core business and portfolio research questions
-- ====================================================================

-- --------------------------------------------------------------------
-- Query 1: Top 5 Industries by Outstanding Credit in the Latest Period
-- Business Question: Where is bank capital predominantly allocated today?
-- --------------------------------------------------------------------
SELECT 
    exposure_rank,
    sector_name,
    credit_outstanding_cr,
    sector_share_pct,
    yoy_growth_pct,
    mom_growth_pct
FROM v_top_sectors_latest
LIMIT 5;

-- --------------------------------------------------------------------
-- Query 2: Fastest Growing Industries Year-over-Year (YoY)
-- Business Question: Which industries are accelerating their bank borrowing?
-- Filters to mutually exclusive sectors with significant exposure (> 20,000 Cr)
-- --------------------------------------------------------------------
SELECT 
    sector_name,
    credit_outstanding_cr AS current_credit_cr,
    previous_year_credit_cr,
    yoy_change_cr,
    yoy_growth_pct,
    sector_share_pct
FROM v_sector_monthly_kpis
WHERE reporting_month = (SELECT MAX(reporting_month) FROM dim_date)
  AND is_mutually_exclusive = 1
  AND credit_outstanding_cr > 20000
ORDER BY yoy_growth_pct DESC
LIMIT 5;

-- --------------------------------------------------------------------
-- Query 3: Multi-Year Portfolio Share Shift (2019 vs 2026)
-- Business Question: Which sectors gained or lost structural portfolio share?
-- --------------------------------------------------------------------
WITH start_period AS (
    SELECT sector_code, sector_name, sector_share_pct AS share_2019_01, credit_outstanding_cr AS credit_2019_01
    FROM v_sector_monthly_kpis
    WHERE reporting_month = '2019-01' AND is_mutually_exclusive = 1
),
end_period AS (
    SELECT sector_code, sector_name, sector_share_pct AS share_2026_06, credit_outstanding_cr AS credit_2026_06
    FROM v_sector_monthly_kpis
    WHERE reporting_month = '2026-06' AND is_mutually_exclusive = 1
)
SELECT 
    s.sector_name,
    ROUND(s.credit_2019_01, 2) AS credit_2019_01_cr,
    ROUND(e.credit_2026_06, 2) AS credit_2026_06_cr,
    ROUND(s.share_2019_01, 2) AS share_2019_pct,
    ROUND(e.share_2026_06, 2) AS share_2026_pct,
    ROUND(e.share_2026_06 - s.share_2019_01, 2) AS share_change_pp,
    ROUND(100.0 * (e.credit_2026_06 - s.credit_2019_01) / s.credit_2019_01, 2) AS total_growth_pct
FROM start_period s
JOIN end_period e ON s.sector_code = e.sector_code
ORDER BY share_change_pp DESC;

-- --------------------------------------------------------------------
-- Query 4: Long-Term Concentration & HHI Trajectory
-- Business Question: Has the industrial portfolio become more or less concentrated?
-- Compares HHI and Top-3 share at annual June intervals
-- --------------------------------------------------------------------
SELECT 
    reporting_month,
    total_industry_credit_cr,
    hhi_index,
    top3_concentration_share_pct,
    largest_sector,
    largest_sector_share_pct
FROM v_industry_concentration_hhi
WHERE reporting_month IN ('2019-06', '2020-06', '2021-06', '2022-06', '2023-06', '2024-06', '2025-06', '2026-06')
ORDER BY reporting_month ASC;

-- --------------------------------------------------------------------
-- Query 5: Structural Break Evaluation (June 2023 vs July 2023)
-- Business Question: Quantify the immediate impact of the July 2023 bank-NBFC merger
-- --------------------------------------------------------------------
SELECT 
    reporting_month,
    calendar_date,
    total_credit_cr,
    mom_change_cr,
    mom_growth_pct,
    yoy_growth_pct
FROM v_total_industry_monthly
WHERE reporting_month IN ('2023-05', '2023-06', '2023-07', '2023-08', '2023-09')
ORDER BY reporting_month ASC;

-- --------------------------------------------------------------------
-- Query 6: Sub-Sector Composition of Infrastructure Credit
-- Business Question: Which sub-industries drive the largest exposure sector?
-- --------------------------------------------------------------------
SELECT 
    k.sector_name AS sub_sector_name,
    k.credit_outstanding_cr,
    ROUND(100.0 * k.credit_outstanding_cr / NULLIF(p.credit_outstanding_cr, 0), 2) AS share_of_infrastructure_pct,
    k.yoy_growth_pct,
    k.mom_growth_pct
FROM v_sector_monthly_kpis k
JOIN v_sector_monthly_kpis p ON p.sector_code = '2.18' AND p.reporting_month = k.reporting_month
WHERE k.parent_code = '2.18'
  AND k.reporting_month = (SELECT MAX(reporting_month) FROM dim_date)
ORDER BY k.credit_outstanding_cr DESC;

-- --------------------------------------------------------------------
-- Query 7: Basic Metals Breakdown: Iron & Steel vs Other Metals
-- --------------------------------------------------------------------
SELECT 
    k.reporting_month,
    k.sector_name,
    k.credit_outstanding_cr,
    k.yoy_growth_pct,
    ROUND(100.0 * k.credit_outstanding_cr / NULLIF(p.credit_outstanding_cr, 0), 2) AS share_of_metals_pct
FROM v_sector_monthly_kpis k
JOIN v_sector_monthly_kpis p ON p.sector_code = '2.13' AND p.reporting_month = k.reporting_month
WHERE k.parent_code = '2.13'
  AND k.reporting_month IN ('2021-06', '2022-06', '2023-06', '2024-06', '2025-06', '2026-06')
ORDER BY k.reporting_month DESC, k.credit_outstanding_cr DESC;
