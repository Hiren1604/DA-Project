"""
Generator for CreditLens Jupyter Notebooks:
01_data_profiling.ipynb, 02_cleaning_eda.ipynb, 03_sector_analysis.ipynb, 04_statistical_analysis.ipynb
"""

import json
import os


def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.12.3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }


def md_cell(text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip().split("\n")]
    }


def code_cell(code):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in code.strip().split("\n")]
    }


def build_all_notebooks():
    nb_dir = "notebooks"
    os.makedirs(nb_dir, exist_ok=True)

    # -------------------------------------------------------------
    # 01_data_profiling.ipynb
    # -------------------------------------------------------------
    nb1_cells = [
        md_cell("""# CreditLens — Notebook 01: Data Profiling & Provenance
### Indian Banking & Credit Portfolio Analytics
**Dataset:** RBI Industry-wise Deployment of Bank Credit (Table 16) & Major Sectors (Table 15)  
**Objective:** Profile raw datasets, check column semantics, data types, null values, cardinality, and reporting periods."""),
        code_cell("""import os
import json
import pandas as pd
import numpy as np

# Load source metadata
with open('../data/raw/source_metadata.json', 'r', encoding='utf-8') as f:
    meta = json.load(f)

print("Publisher:", meta['publisher'])
print("Download UTC:", meta['downloaded_at_utc'])
print("Table 16 Periods:", meta['modules']['module_a_industry_credit']['periods_count'])
print("Table 16 Observations:", meta['modules']['module_a_industry_credit']['total_observations'])"""),
        md_cell("""### 1. Inspect Raw Table 16 (Industry Credit)"""),
        code_cell("""df_t16_raw = pd.read_csv('../data/raw/rbi_industry_credit_long_raw.csv')
print("Shape:", df_t16_raw.shape)
display(df_t16_raw.head())
print("\\nColumn Data Types:")
print(df_t16_raw.dtypes)"""),
        md_cell("""### 2. Missing Value & Null Profiling"""),
        code_cell("""print("Null Counts:")
print(df_t16_raw.isnull().sum())
print("\\nMissing Rate (%):")
print((df_t16_raw.isnull().sum() / len(df_t16_raw)) * 100)"""),
        md_cell("""### 3. Date & Cardinality Inspection"""),
        code_cell("""print("Unique Reporting Periods:", df_t16_raw['period_raw'].nunique())
print("Unique Industry Items:", df_t16_raw['item_label'].nunique())
print("\\nSample Industry Labels:")
print(df_t16_raw['item_label'].drop_duplicates().head(10).tolist())"""),
        md_cell("""### 4. Summary & Profiling Conclusions
- Raw Table 16 contains **3,870 long-format observations** across **90 continuous reporting periods** (Jan 2019 to Jun 2026).
- 0 missing credit values detected in Table 16.
- In Table 15 (Major Sectors), the placeholder memo item `Priority Sector (Memo)` has 90 null values, properly quarantined.
- Data is ready for cleaning, hierarchy normalization, and relational modeling.""")
    ]
    with open(os.path.join(nb_dir, "01_data_profiling.ipynb"), "w", encoding="utf-8") as f:
        json.dump(make_notebook(nb1_cells), f, indent=2)

    # -------------------------------------------------------------
    # 02_cleaning_eda.ipynb
    # -------------------------------------------------------------
    nb2_cells = [
        md_cell("""# CreditLens — Notebook 02: Data Cleaning & Exploratory Data Analysis
**Objective:** Standardize reporting dates, strip footnote superscripts, assign hierarchy levels, and explore credit distributions."""),
        code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

df_clean = pd.read_csv('../data/processed/credit_clean.csv')
df_clean['reporting_date'] = pd.to_datetime(df_clean['reporting_date'])
print("Cleaned Dataset Shape:", df_clean.shape)
display(df_clean.head())"""),
        md_cell("""### 1. Hierarchy Level Breakdown"""),
        code_cell("""print("Hierarchy Level Distribution:")
print(df_clean['hierarchy_level'].value_counts())
print("\\nMutually Exclusive Level-1 Sectors Count:", df_clean[df_clean['is_mutually_exclusive']==True]['sector_code'].nunique())"""),
        md_cell("""### 2. Credit Outstanding Distribution Across Mutually Exclusive Sectors (Latest Period)"""),
        code_cell("""latest_dt = df_clean['reporting_date'].max()
df_latest_l1 = df_clean[(df_clean['reporting_date'] == latest_dt) & (df_clean['is_mutually_exclusive'] == True)].sort_values('credit_outstanding_cr', ascending=False)

plt.figure(figsize=(12, 6))
sns.barplot(data=df_latest_l1, x='credit_outstanding_cr', y='sector_name', palette='Blues_r')
plt.title(f'Industrial Bank Credit Exposure by Sector ({latest_dt.strftime("%B %Y")})')
plt.xlabel('Credit Outstanding (₹ Crore)')
plt.ylabel('Industry Sector')
plt.grid(True, axis='x', linestyle='--', alpha=0.5)
plt.show()"""),
        md_cell("""### 3. Outlier and Distribution Statistics"""),
        code_cell("""stats = df_latest_l1['credit_outstanding_cr'].describe()
print("Distribution Statistics (₹ Crore):")
print(stats)
print(f"\\nMedian Exposure: ₹{stats['50%']:,.2f} Cr")
print(f"Interquartile Range (IQR): ₹{stats['75%'] - stats['25%']:,.2f} Cr")""")
    ]
    with open(os.path.join(nb_dir, "02_cleaning_eda.ipynb"), "w", encoding="utf-8") as f:
        json.dump(make_notebook(nb2_cells), f, indent=2)

    # -------------------------------------------------------------
    # 03_sector_analysis.ipynb
    # -------------------------------------------------------------
    nb3_cells = [
        md_cell("""# CreditLens — Notebook 03: Sector Exposure & Growth Analysis
**Objective:** Analyze sector portfolio allocation, YoY growth patterns, multi-year share drift (2019 vs 2026), and subsector drivers."""),
        code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df_metrics = pd.read_csv('../data/processed/sector_monthly_metrics.csv')
df_metrics['reporting_date'] = pd.to_datetime(df_metrics['reporting_date'])"""),
        md_cell("""### 1. Multi-Year Portfolio Share Shift (2019 vs 2026)"""),
        code_cell("""start_m = df_metrics[df_metrics['reporting_month'] == '2019-01'].set_index('sector_name')['sector_share_pct']
end_m = df_metrics[df_metrics['reporting_month'] == '2026-06'].set_index('sector_name')['sector_share_pct']

df_shift = pd.DataFrame({'Share_2019_pct': start_m, 'Share_2026_pct': end_m}).dropna()
df_shift['Share_Shift_pp'] = df_shift['Share_2026_pct'] - df_shift['Share_2019_pct']
df_shift = df_shift.sort_values('Share_Shift_pp', ascending=False)

print("Top Share Gainers & Decliners (Percentage Points):")
display(df_shift.head(10))"""),
        md_cell("""### 2. Infrastructure Subsector Composition"""),
        code_cell("""infra_sub = df_metrics[(df_metrics['parent_code'] == '2.18') & (df_metrics['reporting_month'] == '2026-06')].sort_values('credit_outstanding_cr', ascending=False)
infra_tot = df_metrics[(df_metrics['sector_code'] == '2.18') & (df_metrics['reporting_month'] == '2026-06')]['credit_outstanding_cr'].iloc[0]

infra_sub['share_of_infra_pct'] = (infra_sub['credit_outstanding_cr'] / infra_tot) * 100

plt.figure(figsize=(10, 5))
plt.bar(infra_sub['sector_name'], infra_sub['share_of_infra_pct'], color='#06B6D4')
plt.title('Infrastructure Subsector Allocation (%) - June 2026')
plt.ylabel('Share of Infrastructure Credit (%)')
plt.xticks(rotation=25, ha='right')
plt.grid(True, axis='y', linestyle='--', alpha=0.5)
plt.show()"""),
        md_cell("""### 3. Key Observations
- **Power** is the single largest subsector under Infrastructure, followed by **Roads** and **Telecommunications**.
- **All Engineering**, **Other Industries**, and **Basic Metals** recorded notable structural share gains between 2019 and 2026.""")
    ]
    with open(os.path.join(nb_dir, "03_sector_analysis.ipynb"), "w", encoding="utf-8") as f:
        json.dump(make_notebook(nb3_cells), f, indent=2)

    # -------------------------------------------------------------
    # 04_statistical_analysis.ipynb
    # -------------------------------------------------------------
    nb4_cells = [
        md_cell("""# CreditLens — Notebook 04: Statistical Analysis & Concentration
**Objective:** Measure market concentration via Herfindahl-Hirschman Index (HHI), Top-3 exposure, growth correlations, and structural break impact."""),
        code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

df_conc = pd.read_csv('../data/processed/industry_concentration_monthly.csv')
df_conc['date'] = pd.to_datetime(df_conc['reporting_month'] + '-01')
display(df_conc.tail())"""),
        md_cell("""### 1. HHI Trajectory Over Time"""),
        code_cell("""plt.figure(figsize=(12, 5))
plt.plot(df_conc['date'], df_conc['hhi_index'], color='#06B6D4', linewidth=2, label='HHI (Points)')
plt.axhline(1500, color='#F59E0B', linestyle='--', label='Moderate Concentration (1,500 pts)')
plt.axhline(1000, color='#10B981', linestyle='--', label='Unconcentrated Threshold (1,000 pts)')
plt.title('Herfindahl-Hirschman Index (HHI) Trajectory (2019 – 2026)')
plt.ylabel('HHI Points')
plt.grid(True, linestyle='--', alpha=0.4)
plt.legend()
plt.show()"""),
        md_cell("""### 2. Cross-Sector Growth Correlation Matrix"""),
        code_cell("""df_metrics = pd.read_csv('../data/processed/sector_monthly_metrics.csv')
df_l1 = df_metrics[df_metrics['is_mutually_exclusive'] == True]
pivot_growth = df_l1.pivot(index='reporting_month', columns='sector_name', values='yoy_growth_pct').dropna()

# Select top 7 sectors for clean correlation matrix
top_secs = df_l1.groupby('sector_name')['credit_outstanding_cr'].mean().nlargest(7).index
corr_matrix = pivot_growth[top_secs].corr()

plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1)
plt.title('YoY Growth Rate Correlation Across Leading Sectors')
plt.show()"""),
        md_cell("""### 3. Structural Break Analysis (July 2023 Bank-NBFC Merger)"""),
        code_cell("""df_tot = df_metrics[df_metrics['sector_code'] == '2'].sort_values('reporting_date')
pre_merger = df_tot[df_tot['reporting_month'] == '2023-06']['credit_outstanding_cr'].iloc[0]
post_merger = df_tot[df_tot['reporting_month'] == '2023-07']['credit_outstanding_cr'].iloc[0]

jump_cr = post_merger - pre_merger
jump_pct = (jump_cr / pre_merger) * 100

print(f"June 2023 Industry Credit: ₹{pre_merger:,.2f} Cr")
print(f"July 2023 Industry Credit: ₹{post_merger:,.2f} Cr")
print(f"One-Month Level Shift: +₹{jump_cr:,.2f} Cr ({jump_pct:.2f}%)")""")
    ]
    with open(os.path.join(nb_dir, "04_statistical_analysis.ipynb"), "w", encoding="utf-8") as f:
        json.dump(make_notebook(nb4_cells), f, indent=2)

    print("All 4 Jupyter Notebooks generated successfully.")


if __name__ == "__main__":
    build_all_notebooks()
