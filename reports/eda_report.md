# CreditLens — Exploratory Data Analysis (EDA) Report

## 1. Executive Summary
This report presents exploratory data analysis on the **Indian Banking Industry Credit Dataset** obtained from the Reserve Bank of India (RBI) Database on Indian Economy (DBIE).
The analysis spans **90 uninterrupted consecutive reporting months** from **January 2019 to June 2026**, covering **3,870 detailed observations** across 19 mutually exclusive industries and 23 sub-categories.

---

## 2. Dataset Shape & Provenance
- **Publisher:** Reserve Bank of India (RBI)
- **Primary Source:** DBIE Table 16 — *Industry-wise Deployment of Bank Credit*
- **Supplementary Source:** DBIE Table 15 — *Deployment of Gross Bank Credit by Major Sectors*
- **Total Processed Rows:** 3,870 (Table 16) + 3,960 (Table 15) = 7,830 rows
- **Time Horizon:** January 18, 2019 to June 30, 2026 (7.5 years)
- **Data Unit:** ₹ crore (INR Cr)

---

## 3. Data Integrity & Validation Findings
All 3,870 industry observations successfully passed 6 deterministic data validation checks:
1. **Date Validity (VR-01):** 100% valid datetime timestamps; zero nulls.
2. **Numeric Completeness (VR-02):** Zero missing credit values in Table 16. (In Table 15, 90 placeholder rows for *Priority Sector Memo* were quarantined with status `review`).
3. **Non-Negative Values (VR-03):** 100% of reported credit figures are non-negative.
4. **Natural Key Uniqueness (VR-04):** Zero duplicated `(reporting_date, sector_code)` pairs.
5. **Time-Series Continuity (VR-05):** Zero missing calendar months; full 90-month continuous coverage.
6. **Hierarchy Aggregation Integrity (VR-06):** In every single month, the sum of the 19 mutually exclusive Level-1 sectors equals the official Grand Total (Code 2) within a tight rounding tolerance `<= 2.0 Cr` (mean discrepancy = `0.11 Cr`).

---

## 4. Key Statistical Findings

### 4.1 Overall Industrial Credit Scale
- **Total Outstanding Credit (Jan 2019):** ₹27,15,406.47 Cr (~₹27.15 Lakh Cr)
- **Total Outstanding Credit (Jun 2026):** ₹47,71,513.11 Cr (~₹47.72 Lakh Cr)
- **Net Capital Expansion:** +₹20,56,106.64 Cr (+75.72% cumulative expansion over 7.5 years)
- **Compound Annual Growth Rate (CAGR):** ~8.04% per annum.

### 4.2 Cross-Sectional Distribution (June 2026)
- **Top Sector:** **Infrastructure** with **₹15,11,787.18 Cr** (31.68% of total industrial credit).
- **Second Largest:** **Basic Metal & Metal Product** with **₹5,34,392.02 Cr** (11.20%).
- **Third Largest:** **Other Industries** with **₹3,74,052.04 Cr** (7.84%).
- **Smallest Exposure:** **Leather & Leather Products** with **₹14,562.07 Cr** (0.31%).
- **Distribution Shape:** High positive skewness; mean sector exposure (₹2,51,132 Cr) is substantially higher than the median exposure (₹68,922 Cr).

### 4.3 Market Concentration Trajectory
- **Herfindahl-Hirschman Index (HHI):**
  - January 2019: **1,858.9 points** (Highly concentrated, driven by Power and Infrastructure loans).
  - June 2023: **1,412.5 points** (Gradual diversification into manufacturing and chemicals).
  - June 2026: **1,431.3 points** (Stabilized in the moderately concentrated range).
- **Top 3 Sectors Concentration Share:**
  - January 2019: **55.94%** (Infrastructure, Basic Metals, Textiles).
  - June 2026: **50.72%** (Infrastructure, Basic Metals, Other Industries).
  - Concentration dropped by **5.22 percentage points**, reflecting steady diversification across mid-tier engineering and manufacturing sectors.

---

## 5. Structural Breaks & Anomaly Analysis
1. **July 2023 Bank-NBFC Merger Step-Up:**
   - In July 2023, the merger of HDFC Ltd. into HDFC Bank took effect.
   - Total industrial credit registered an immediate shift from ₹34.48 Lakh Cr (June 2023) to ₹33.81 Lakh Cr in July followed by rapid expansion to ₹35.57 Lakh Cr by November 2023.
   - Personal loans and commercial services in Table 15 showed an immediate upward shift of over ₹3.5 Lakh Cr.
2. **Post-Pandemic Credit Surge (2022 – 2023):**
   - Annual growth peaked between mid-2022 and early 2023, reaching over 12% YoY, before accelerating to over 19% YoY by mid-2026.
