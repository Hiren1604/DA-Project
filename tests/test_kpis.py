"""
Unit tests for financial KPI calculations, growth metrics, and concentration measures.
"""

import numpy as np
import pandas as pd
import sqlite3
from excel.generate_reconciliation_excel import reconciliation_status


def test_mom_growth_calculation(metrics_df):
    """Test MoM formula: (curr - prev) / prev * 100."""
    sample = metrics_df[metrics_df["previous_month_credit_cr"].notna() & (metrics_df["previous_month_credit_cr"] > 0)].copy()
    expected_growth = (sample["credit_outstanding_cr"] - sample["previous_month_credit_cr"]) / sample["previous_month_credit_cr"] * 100.0
    diff = (sample["mom_growth_pct"] - expected_growth).abs()
    assert (diff < 1e-4).all()


def test_yoy_growth_calculation(metrics_df):
    """Test YoY formula: (curr - prev_year) / prev_year * 100."""
    sample = metrics_df[metrics_df["previous_year_credit_cr"].notna() & (metrics_df["previous_year_credit_cr"] > 0)].copy()
    expected_growth = (sample["credit_outstanding_cr"] - sample["previous_year_credit_cr"]) / sample["previous_year_credit_cr"] * 100.0
    diff = (sample["yoy_growth_pct"] - expected_growth).abs()
    assert (diff < 1e-4).all()


def test_sector_share_sum_100(metrics_df):
    """Verify that the sum of the 19 mutually exclusive sector shares equals 100% (+/- 0.05%)."""
    df_l1 = metrics_df[metrics_df["is_mutually_exclusive"] == True]
    monthly_share_sums = df_l1.groupby("reporting_month")["sector_share_pct"].sum()
    for month, total_share in monthly_share_sums.items():
        assert abs(total_share - 100.0) < 0.05, f"Sector share sum in {month} was {total_share}%"


def test_hhi_calculation(concentration_df, metrics_df):
    """Verify HHI calculation against manual sum of squared fractional shares."""
    df_l1 = metrics_df[metrics_df["is_mutually_exclusive"] == True]
    for _, row in concentration_df.iterrows():
        month = row["reporting_month"]
        month_group = df_l1[df_l1["reporting_month"] == month]
        tot_credit = month_group["credit_outstanding_cr"].sum()
        shares = month_group["credit_outstanding_cr"] / tot_credit
        expected_hhi_pts = round(((shares * 100) ** 2).sum(), 2)
        assert abs(row["hhi_index"] - expected_hhi_pts) < 0.1


def test_top3_concentration_bounds(concentration_df):
    """Assert top 3 concentration share is strictly between 0 and 100%."""
    assert (concentration_df["top3_concentration_share_pct"] > 30.0).all()
    assert (concentration_df["top3_concentration_share_pct"] < 80.0).all()


def test_sqlite_calendar_month_rollover():
    """SQL month matching must handle month ends and leap-year dates."""
    cases = {
        "2019-03-31": ("2019-02", "2018-03"),
        "2020-03-31": ("2020-02", "2019-03"),
        "2021-05-31": ("2021-04", "2020-05"),
        "2024-01-31": ("2023-12", "2023-01"),
    }
    with sqlite3.connect(":memory:") as conn:
        for date_value, expected in cases.items():
            actual = conn.execute(
                "SELECT strftime('%Y-%m', date(?, 'start of month', '-1 month')), "
                "strftime('%Y-%m', date(?, 'start of month', '-1 year'))",
                (date_value, date_value),
            ).fetchone()
            assert actual == expected


def test_reconciliation_flags_injected_sql_error():
    """A deliberately wrong SQL output must be detected by the independent audit."""
    assert reconciliation_status([19.24, 19.24, 19.24]) == "MATCH"
    assert reconciliation_status([19.24, 18.24, 19.24]) == "MISMATCH"
