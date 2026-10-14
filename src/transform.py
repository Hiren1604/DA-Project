"""
Transformation and KPI Calculation Module for CreditLens.
Computes month-over-month (MoM) and year-over-year (YoY) credit growth,
sector portfolio allocation shares, Herfindahl-Hirschman Index (HHI),
top-3 concentration ratios, indexed growth series, and historical peak flags.
"""

import os
import pandas as pd
import numpy as np


def compute_monthly_metrics(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Compute core financial and portfolio metrics for each sector and reporting period.
    """
    df = df_clean.copy()
    df["reporting_date"] = pd.to_datetime(df["reporting_date"])
    df["period_m"] = df["reporting_date"].dt.to_period("M")

    # Grand total credit per month (from Code 2)
    grand_totals = df[df["sector_code"] == "2"].set_index("period_m")["credit_outstanding_cr"].to_dict()
    df["grand_total_industry_credit_cr"] = df["period_m"].map(grand_totals)

    # Sector share % (against Total Industry Credit)
    df["sector_share_pct"] = np.where(
        df["grand_total_industry_credit_cr"] > 0,
        (df["credit_outstanding_cr"] / df["grand_total_industry_credit_cr"]) * 100.0,
        np.nan
    )

    # Calendar period joins for MoM (t - 1 month) and YoY (t - 12 months)
    # Create lookup map: (sector_code, period_m) -> credit_outstanding_cr
    val_map = df.set_index(["sector_code", "period_m"])["credit_outstanding_cr"].to_dict()

    df["prev_month_period"] = df["period_m"] - 1
    df["prev_year_period"] = df["period_m"] - 12

    # Map previous values
    df["previous_month_credit_cr"] = df.apply(
        lambda r: val_map.get((r["sector_code"], r["prev_month_period"])), axis=1
    )
    df["previous_year_credit_cr"] = df.apply(
        lambda r: val_map.get((r["sector_code"], r["prev_year_period"])), axis=1
    )

    # MoM changes
    df["mom_change_cr"] = df["credit_outstanding_cr"] - df["previous_month_credit_cr"]
    df["mom_growth_pct"] = np.where(
        df["previous_month_credit_cr"] > 0,
        (df["mom_change_cr"] / df["previous_month_credit_cr"]) * 100.0,
        np.nan
    )

    # YoY changes
    df["yoy_change_cr"] = df["credit_outstanding_cr"] - df["previous_year_credit_cr"]
    df["yoy_growth_pct"] = np.where(
        df["previous_year_credit_cr"] > 0,
        (df["yoy_change_cr"] / df["previous_year_credit_cr"]) * 100.0,
        np.nan
    )

    # Base 100 Indexed series (Base = Jan 2019)
    base_period = pd.Period("2019-01", freq="M")
    base_val_map = df[df["period_m"] == base_period].set_index("sector_code")["credit_outstanding_cr"].to_dict()
    df["base_credit_2019_01_cr"] = df["sector_code"].map(base_val_map)
    df["credit_indexed_base100"] = np.where(
        df["base_credit_2019_01_cr"] > 0,
        (df["credit_outstanding_cr"] / df["base_credit_2019_01_cr"]) * 100.0,
        np.nan
    )

    # Historical Peak Flag (whether credit outstanding is an all-time high up to this month)
    df = df.sort_values(by=["sector_code", "reporting_date"]).reset_index(drop=True)
    df["historical_cummax"] = df.groupby("sector_code")["credit_outstanding_cr"].cummax()
    df["is_historical_peak"] = (df["credit_outstanding_cr"] >= df["historical_cummax"]) & df["credit_outstanding_cr"].notna()

    # Drop temporary period helper columns
    df = df.drop(columns=["period_m", "prev_month_period", "prev_year_period", "historical_cummax"])

    return df


def compute_concentration_metrics(df_metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Herfindahl-Hirschman Index (HHI) and Top-3 Concentration Share
    for each reporting month across the 19 mutually exclusive sectors.
    """
    # Filter strictly to the 19 mutually exclusive Level-1 sectors
    df_l1 = df_metrics[df_metrics["is_mutually_exclusive"] == True].copy()

    records = []
    for month, group in df_l1.groupby("reporting_month"):
        tot_credit = group["credit_outstanding_cr"].sum()
        shares = group["credit_outstanding_cr"] / tot_credit  # fractional shares summing to 1.0

        # Standard HHI (sum of squared percentage points, scale 0 - 10,000)
        hhi_pts = ((shares * 100) ** 2).sum()
        # Fractional HHI (0 - 1.0 scale)
        hhi_fraction = (shares ** 2).sum()

        # Top 3 sectors by credit
        top3 = group.sort_values(by="credit_outstanding_cr", ascending=False).head(3)
        top3_credit = top3["credit_outstanding_cr"].sum()
        top3_share_pct = (top3_credit / tot_credit) * 100.0
        top3_names = ", ".join(top3["sector_name"].tolist())

        # Largest single sector
        largest_sec = top3.iloc[0]["sector_name"] if len(top3) > 0 else ""
        largest_sec_share = (top3.iloc[0]["credit_outstanding_cr"] / tot_credit) * 100.0 if len(top3) > 0 else 0

        records.append({
            "reporting_month": month,
            "total_mutually_exclusive_credit_cr": round(tot_credit, 2),
            "hhi_index": round(hhi_pts, 2),
            "hhi_fraction": round(hhi_fraction, 4),
            "top3_concentration_share_pct": round(top3_share_pct, 2),
            "top3_sectors": top3_names,
            "largest_sector": largest_sec,
            "largest_sector_share_pct": round(largest_sec_share, 2)
        })

    return pd.DataFrame(records)


def run_transformations(data_dir: str = "data") -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Execute full KPI transformation pipeline and persist results.
    """
    proc_dir = os.path.join(data_dir, "processed")
    clean_path = os.path.join(proc_dir, "credit_clean.csv")

    df_clean = pd.read_csv(clean_path)
    df_metrics = compute_monthly_metrics(df_clean)
    df_conc = compute_concentration_metrics(df_metrics)

    # Merge concentration metrics into sector monthly metrics for easy slicing
    df_metrics_enriched = df_metrics.merge(
        df_conc[["reporting_month", "hhi_index", "top3_concentration_share_pct", "largest_sector"]],
        on="reporting_month",
        how="left"
    )

    metrics_csv_path = os.path.join(proc_dir, "sector_monthly_metrics.csv")
    df_metrics_enriched.to_csv(metrics_csv_path, index=False, encoding="utf-8")

    conc_csv_path = os.path.join(proc_dir, "industry_concentration_monthly.csv")
    df_conc.to_csv(conc_csv_path, index=False, encoding="utf-8")

    return df_metrics_enriched, df_conc


if __name__ == "__main__":
    m1, m2 = run_transformations()
    print("Transformations completed successfully.")
    print("Metrics rows:", len(m1))
    print("Concentration monthly series rows:", len(m2))
    latest = m2.iloc[-1]
    print(f"Latest Month: {latest['reporting_month']}")
    print(f"  HHI: {latest['hhi_index']}")
    print(f"  Top 3 Share: {latest['top3_concentration_share_pct']}% ({latest['top3_sectors']})")
    print(f"  Largest Sector: {latest['largest_sector']} ({latest['largest_sector_share_pct']}%)")
