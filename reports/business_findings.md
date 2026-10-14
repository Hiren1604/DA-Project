# CreditLens — Analytical Business Findings Report

This report presents five evidence-backed financial findings derived strictly from the **Reserve Bank of India (RBI) DBIE** industrial credit dataset. Every observation is quantified with exact reporting dates, monetary values in ₹ crore, percentage movements, and methodological considerations.

---

### Finding 1: Infrastructure Dominates Total Exposure but Loses Relative Portfolio Share
- **Reporting Period:** June 2026 vs June 2025 and January 2019
- **Sector:** Infrastructure (Code 2.18)
- **Current Credit Outstanding (June 2026):** ₹15,11,787.18 crore (~₹15.12 Lakh Cr)
- **Baseline Credit (June 2025):** ₹13,63,380.18 crore
- **Baseline Credit (January 2019):** ₹9,78,060.52 crore
- **Absolute Change:** +₹1,48,407.00 crore YoY; +₹5,33,726.66 crore over the 7.5-year horizon.
- **Percentage Change:** +10.89% YoY; +54.57% total expansion since Jan 2019.
- **Portfolio Share Movement:** Decreased from **36.02%** in January 2019 to **31.68%** in June 2026 (**-4.34 percentage points**).
- **Supporting Visual:** `assets/dashboard_screenshots/executive_credit_overview.png`
- **Analytical Interpretation:** While Infrastructure remains by far the single largest sector in Indian banking (representing almost 1/3rd of all outstanding industrial loans), its relative portfolio share has steadily receded. Bank lending has expanded more aggressively into engineering, basic metals, and specialty manufacturing, resulting in a broader distribution of banking assets.
- **Limitations:** Infrastructure includes long-gestation public-private partnerships (Power, Roads, Telecom). Aggregated outstanding credit does not reflect refinancing or bond market disintermediation.
- **Follow-up Recommendation:** Disaggregate Infrastructure sub-sectors (Power vs Roads vs Telecom) to evaluate whether declining share is driven by power sector deleveraging or increased infrastructure debt funds (IDFs).

---

### Finding 2: All Engineering Surges as the Fastest-Growing Major Industrial Segment
- **Reporting Period:** June 2026 vs June 2025
- **Sector:** All Engineering (Code 2.14)
- **Current Credit Outstanding (June 2026):** ₹3,42,309.11 crore (~₹3.42 Lakh Cr)
- **Comparison Amount (June 2025):** ₹2,48,780.84 crore
- **Absolute Change:** +₹93,528.27 crore YoY
- **Percentage Change:** **+37.59% YoY** (highest annual expansion among all major sectors > ₹1 Lakh Cr)
- **Portfolio Share Movement:** Increased from **6.11%** (Jan 2019) to **7.17%** (Jun 2026), gaining **+1.06 percentage points**.
- **Supporting Visual:** `assets/dashboard_screenshots/sector_indexed_growth.png`
- **Analytical Interpretation:** The 37.59% surge in engineering credit outstanding reflects substantial capacity expansion in capital goods, defense manufacturing, electronics, and heavy machinery, outpacing broader industrial credit growth (+19.24% YoY).
- **Limitations:** Data reflects gross scheduled commercial bank loans and does not isolate working capital utilization from term debt for capex.
- **Follow-up Recommendation:** Cross-reference Engineering credit growth with the Index of Industrial Production (IIP) for Capital Goods to verify whether borrowing is driving capacity addition or financing inventory buildup.

---

### Finding 3: Basic Metal & Metal Product Expands to Second-Largest Exposure Sector
- **Reporting Period:** June 2026 vs June 2025
- **Sector:** Basic Metal & Metal Product (Code 2.13)
- **Current Credit Outstanding (June 2026):** ₹5,34,392.02 crore (~₹5.34 Lakh Cr)
- **Comparison Amount (June 2025):** ₹4,42,054.87 crore
- **Absolute Change:** +₹92,337.15 crore YoY
- **Percentage Change:** **+20.89% YoY**
- **Sub-Sector Driver:** **Iron & Steel** (Code 2.13.1) accounts for **₹3,68,672.62 crore** (68.99% of Basic Metals credit), expanding +22.28% YoY from ₹3,01,600.00 crore.
- **Supporting Visual:** `assets/dashboard_screenshots/executive_credit_overview.png`
- **Analytical Interpretation:** Strong domestic infrastructure demand and brownfield steel mill expansions have driven heavy commercial bank exposure to steel producers. Basic Metals now commands 11.20% of all industrial bank credit.
- **Limitations:** Steel borrowing is cyclical and sensitive to global coking coal and raw material commodity pricing.
- **Follow-up Recommendation:** Monitor credit exposure against global steel price benchmarks and capacity utilization rates published by the Joint Plant Committee (JPC).

---

### Finding 4: Industrial Credit Concentration (HHI) De-escalates to Moderate Levels
- **Reporting Period:** January 2019 to June 2026
- **Metric:** Herfindahl-Hirschman Index (HHI) and Top 3 Sectors Concentration Share
- **HHI Movement:** Dropped from **1,713.93 points** (Jan 2019) to **1,431.30 points** (Jun 2026) (**-282.63 points**).
- **Top 3 Sectors Share Movement:** Decreased from **56.84%** (Jan 2019) to **50.72%** (Jun 2026) (**-6.12 percentage points**).
- **Top 3 Sectors (Jun 2026):** Infrastructure (31.68%), Basic Metals (11.20%), and Other Industries (7.84%).
- **Supporting Visual:** `assets/dashboard_screenshots/sector_exposure_concentration.png`
- **Analytical Interpretation:** The Indian industrial credit portfolio has structurally de-concentrated over the 7.5-year window. The HHI has moved from the borderline high-concentration territory (> 1,700 points) firmly down into the moderate concentration band (< 1,500 points). This reflects healthier portfolio diversification across mid-scale manufacturing and consumer industries.
- **Limitations:** HHI is calculated across the 19 mutually exclusive RBI Level-1 sectors. If calculated at sub-sector level, HHI would be lower due to finer granularity.
- **Follow-up Recommendation:** Establish an automated internal risk alert threshold at HHI = 1,600 points to trigger capital allocation reviews.

---

### Finding 5: July 2023 Bank-NBFC Merger Created a Structural Benchmark Break
- **Reporting Period:** July 2023 vs June 2023
- **Sector:** Gross Bank Credit & Scheduled Commercial Bank Universe
- **Observation:** On July 28, 2023, the merger of HDFC Ltd. (a housing finance non-bank) into HDFC Bank took effect.
- **Observed Impact:**
  - Table 15 (Major Sectors) non-food bank credit registered an immediate structural level shift of over **₹3.5 Lakh crore** in a single month as mortgage books transitioned onto commercial bank balance sheets.
  - Commercial Real Estate and Personal Loans showed instantaneous double-digit jumps.
- **Supporting Visual:** `assets/dashboard_screenshots/growth_heatmap.png`
- **Analytical Interpretation:** Any naive calculation of 12-month trailing growth spanning July 2023 (e.g. comparing June 2024 to June 2023) captures both organic banking loan expansion and the one-off inorganic reclassification of NBFC loan assets into commercial bank credit.
- **Limitations:** Official DBIE aggregate releases incorporate the merged entity from July 2023 onward without retroactive adjustment of earlier historical series.
- **Follow-up Recommendation:** Multi-year models spanning 2023 must either annotate the July 2023 structural break or present merged vs pre-merger adjusted growth rates to avoid misinterpreting reporting breaks as economic surges.
