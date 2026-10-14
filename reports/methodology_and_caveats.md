# CreditLens — Methodology, Governance & Technical Caveats

## 1. Primary Source Governance
All statistical observations processed in the CreditLens system originate from official statistical releases by the **Reserve Bank of India (RBI)**, accessible via the *Database on Indian Economy (DBIE)* portal.

- **Table 16:** *Industry-wise Deployment of Bank Credit*  
  [Official DBIE URL](https://dbie.rbihub.in/banking/bank-credit-by-industry)
- **Table 15:** *Deployment of Gross Bank Credit by Major Sectors*  
  [Official DBIE URL](https://dbie.rbihub.in/banking/bank-credit-by-sector)

---

## 2. Institutional Reporting Scope & Boundaries
Users, data analysts, and risk reviewers should be cognizant of the following scope limitations:

1. **Aggregate Banking Series vs Loan-Level Credit Risk:**
   - The RBI deployment dataset represents the **aggregate outstanding stock of credit** deployed by scheduled commercial banks (SCBs) to broad economic sectors.
   - It is **not** a transaction-level, loan-level, or borrower-level dataset.
   - It **cannot** measure individual borrower defaults, Probability of Default (PD), Loss Given Default (LGD), non-performing asset (NPA) recoveries, credit scores, or realized credit loss distributions.
   - Any attempt to train default prediction models directly on this dataset alone constitutes an analytical anti-pattern.

2. **Bank Coverage Scope:**
   - Data relates to select 41 Scheduled Commercial Banks (SCBs), accounting for approximately 90% of total non-food credit extended by all scheduled commercial banks.
   - Credit extended by Regional Rural Banks (RRBs), Urban Cooperative Banks (UCBs), small finance banks, or pure non-banking financial companies (NBFCs) is excluded unless explicitly noted in supplementary tables.

---

## 3. Structural Methodological Breaks

### Break A: January 2019 Format Revision
With effect from January 2019, RBI sectoral credit data transitioned to a revised reporting format. Due to this reclassification, certain sub-component series published prior to January 2019 underwent definitional changes. For analytical integrity and clean comparability, CreditLens focuses its primary time-series fact table on the continuous post-January 2019 revised series (spanning January 2019 to June 2026).

### Break B: July 28, 2023 Bank-NBFC Merger (HDFC)
Effective July 28, 2023, the dataset includes the impact of the merger of a non-bank housing finance corporation (HDFC Ltd.) with a scheduled commercial bank (HDFC Bank).
- This event introduced an inorganic, one-off level shift into aggregate bank credit outstanding, particularly in Housing, Commercial Real Estate, and Non-Food Credit.
- Growth rates computed across the July 2023 boundary (e.g., comparing periods in late 2023 / early 2024 to early 2023) reflect both organic lending expansion and the absorption of the NBFC balance sheet.
- All analytical visuals and SQL KPI views in CreditLens explicitly annotate this transition date.

---

## 4. Hierarchy & Double-Counting Safeguards
RBI deployment tables feature a nested taxonomy:
- **Level 0 (Grand Total):** Code `2` (*Industries (2.1 to 2.19)*) representing the aggregate exposure.
- **Level 1 (Sector Totals):** Codes `2.1` to `2.19` representing 19 mutually exclusive industry groups.
- **Level 2 (Sub-Sectors):** Codes `2.2.1`, `2.18.1`, etc. representing sub-categories within parent industries.

**Critical Rule:** To prevent double-counting, portfolio share calculations, HHI concentration indices, and top-sector rankings must strictly isolate the **19 mutually exclusive Level-1 sectors** (`is_mutually_exclusive = TRUE`). Never aggregate parent totals with nested children.
