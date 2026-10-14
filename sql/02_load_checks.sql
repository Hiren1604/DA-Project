-- ====================================================================
-- CreditLens Post-Load Verification and Data Integrity Checks
-- ====================================================================

-- 1. Total Loaded Records Verification
SELECT 
    'fact_credit_outstanding' AS table_name, 
    COUNT(*) AS row_count 
FROM fact_credit_outstanding
UNION ALL
SELECT 'dim_sector', COUNT(*) FROM dim_sector
UNION ALL
SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL
SELECT 'data_quality_exceptions', COUNT(*) FROM data_quality_exceptions;

-- 2. Uniqueness of Natural Key in Fact Table
-- Must return 0 rows
SELECT 
    date_id, 
    sector_id, 
    COUNT(*) AS duplicate_count
FROM fact_credit_outstanding
GROUP BY date_id, sector_id
HAVING COUNT(*) > 1;

-- 3. Referential Integrity Check
-- Must return 0 rows
SELECT f.observation_id
FROM fact_credit_outstanding f
LEFT JOIN dim_date d ON f.date_id = d.date_id
LEFT JOIN dim_sector s ON f.sector_id = s.sector_id
WHERE d.date_id IS NULL OR s.sector_id IS NULL;

-- 4. Check for Negative Outstanding Credit
-- Must return 0 rows
SELECT *
FROM fact_credit_outstanding
WHERE credit_outstanding_cr < 0;

-- 5. Hierarchy Sum Reconciliation (Grand Total vs Sum of Level-1 Mutually Exclusive Sectors)
-- Compares official Grand Total (code 2) with sum of 19 component sectors (codes 2.1 to 2.19)
WITH sector_sums AS (
    SELECT 
        d.reporting_month,
        d.calendar_date,
        SUM(CASE WHEN s.sector_code = '2' THEN f.credit_outstanding_cr ELSE 0 END) AS grand_total_cr,
        SUM(CASE WHEN s.is_mutually_exclusive = 1 THEN f.credit_outstanding_cr ELSE 0 END) AS sum_mutually_exclusive_cr
    FROM fact_credit_outstanding f
    JOIN dim_date d ON f.date_id = d.date_id
    JOIN dim_sector s ON f.sector_id = s.sector_id
    GROUP BY d.reporting_month, d.calendar_date
)
SELECT 
    reporting_month,
    calendar_date,
    grand_total_cr,
    sum_mutually_exclusive_cr,
    ROUND(ABS(grand_total_cr - sum_mutually_exclusive_cr), 2) AS absolute_discrepancy_cr,
    CASE 
        WHEN ABS(grand_total_cr - sum_mutually_exclusive_cr) <= 2.5 THEN 'PASSED'
        ELSE 'RECONCILIATION_FAIL'
    END AS reconciliation_status
FROM sector_sums
ORDER BY reporting_month DESC;

-- 6. Quality Status Distribution
SELECT 
    quality_status, 
    COUNT(*) AS observation_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_credit_outstanding), 2) AS percentage
FROM fact_credit_outstanding
GROUP BY quality_status;
