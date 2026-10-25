# CreditLens — Power BI Dashboard Design & UX Specification

## 1. Design Philosophy
CreditLens is modeled as an **institutional banking research portal** rather than a casual marketing dashboard.
The interface utilizes an intentional Indian financial palette with high contrast, tabular numerals, explicit currency and growth units, and defensive data hierarchy safeguards.

### Color System
| Role | Hex | RGB | Usage |
|---|---|---|---|
| Deep Navy | `#101C30` | `16, 28, 48` | Primary navigation, headers, dark surfaces |
| Slate Blue | `#233B59` | `35, 59, 89` | Card backgrounds, visual containers |
| Cyan Accent | `#06B6D4` | `6, 182, 212` | Active selections, primary trend lines |
| Teal Positive | `#14B8A6` | `20, 184, 166` | Positive annual expansion, top ranking bars |
| Amber Caution | `#F59E0B` | `245, 158, 11` | Moderate concentration alerts, structural break annotations |
| Canvas Off-White | `#F8FAFC` | `248, 250, 252` | Main page canvas (light mode) / Background `#0D1525` (dark mode) |
| Grid & Borders | `#1E293B` | `30, 41, 59` | Clean partition borders |

---

## 2. Report Architecture: Introduction + Three Analysis Pages

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│ CreditLens: Indian Banking & Credit Analytics                      RBI DBIE     │
│ [Page 1: Executive Overview]  [Page 2: Sector Exposure]  [Page 3: Trends & QA]  │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Global Slicer: Reporting Period [ June 2026 v ]    Hierarchy Filter: [ Level 1 v]│
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Introduction — Start Here
- **Role:** Default landing page for new readers; it explains the purpose and safe reading order before analysis.
- **Content:** Three question-led routes for credit scale, sector allocation and concentration; a short Table 15 / Table 16 scope note; and hierarchy double-counting guidance.
- **Visual style:** CreditLens-Institutional imported theme, with Segoe UI typography, navy hero, cyan, teal and amber accents.

### Page 1 — Executive Credit Overview
- **User Question:** What is the overall scale and expansion rate of Indian industrial bank credit?
- **Visuals:**
  1. **Top KPI Ribbon:**
     - Total Industry Credit: `₹47.72 Lakh Cr`
     - YoY Credit Growth: `+19.24%`
     - MoM Credit Growth: `+3.19%`
     - Top 3 Concentration: `50.72%`
  2. **Chart A (Left):** Historical Industrial Credit Trajectory (Line + Area chart from 2019 to 2026 with July 2023 Merger annotation).
  3. **Chart B (Right):** Ranked Top 8 Industry Exposures (Horizontal bar chart, formatted in ₹ Lakh Cr).
  4. **Chart C (Bottom Left):** YoY Growth % for Leading Industries (Bar chart).
  5. **Chart D (Bottom Right):** Portfolio Concentration Donut (Top 3 sectors vs remaining 16 sectors).

### Page 2 — Sector Exposure & Concentration
- **User Question:** Where is bank credit concentrated, and how has portfolio allocation shifted?
- **Visuals:**
  1. **Ranked Exposure Matrix:** All 19 Level-1 sectors with Credit Outstanding, Sector Share %, MoM Growth %, YoY Growth %, and Rank.
  2. **HHI Concentration Time Series:** Monthly trend of Herfindahl-Hirschman Index with 1,000 (unconcentrated) and 1,500 (moderately concentrated) threshold reference lines.
  3. **Top 3 Sectors Share Trajectory:** Area chart showing movement in top 3 industry concentration from 2019 to 2026.
  4. **Infrastructure Sub-Sector Decomposition:** Breakdown of the single largest sector (`₹15.12 Lakh Cr`) across Power, Roads, Telecom, Airports, Ports, and Railways.

### Page 3 — Historical Trends & Data Quality
- **User Question:** How do sector growth rates compare on a normalized baseline, and what source caveats apply?
- **Visuals:**
  1. **Indexed Sector Growth Chart:** Base-100 indexed line chart from January 2019 to June 2026 comparing relative expansion.
  2. **Monthly YoY Growth Heatmap:** Month × Year grid highlighting credit cycles, post-pandemic recovery, and the July 2023 merger step-up.
  3. **Data Quality & Exception Audit Grid:** Summary of 13 validation checks (VR-01 to VR-07 across both datasets), showing industry quality results and quarantined Table 15 memo rows.
  4. **Analyst Notes & Methodology Disclaimers:** Visible caveats regarding aggregate bank series vs borrower default risk, and SCB reporting scope.

---

## 3. Interaction & Filter Behavior
- **Default State:** Defaults to the latest available reporting month (`June 2026`), never an artificial live mock.
- **Hierarchy Safety:** Mutually exclusive filter (`IsMutuallyExclusive = TRUE`) enforced on all portfolio share visuals to prevent parent-child double-counting.
- **Cross-Filtering:** Selecting an industry on Page 1 cross-filters Page 2 and Page 3 seamlessly.
- **One-Click Reset:** "Clear All Slicers" action button located in the top navigation header.
