"""
Unit tests for data validation rules and audit checks.
"""

import os
import pandas as pd
from src.validate import validate_dataset


def test_uniqueness_of_natural_key(clean_industry_df):
    duplicates = clean_industry_df.duplicated(subset=["reporting_date", "sector_code"])
    assert not duplicates.any(), "Duplicate reporting_date and sector_code pairs found!"


def test_hierarchy_reconciliation_zero_error(clean_industry_df):
    """Verify that Level 1 sectors sum to Grand Total within rounding error (<= 2.5 Cr)."""
    level_1_codes = [f"2.{i}" for i in range(1, 20)]
    grand_totals = clean_industry_df[clean_industry_df["sector_code"] == "2"].set_index("reporting_date")["credit_outstanding_cr"]
    sum_level1 = clean_industry_df[clean_industry_df["sector_code"].isin(level_1_codes)].groupby("reporting_date")["credit_outstanding_cr"].sum()

    diffs = (grand_totals - sum_level1).abs()
    assert (diffs <= 2.5).all(), f"Hierarchy sum discrepancy exceeded 2.5 Cr: {diffs.max()}"


def test_continuity_90_consecutive_months(clean_industry_df):
    """Verify 90 uninterrupted consecutive reporting months from 2019-01 to 2026-06."""
    obs_months = set(clean_industry_df["reporting_month"].unique())
    expected_months = set(pd.period_range(start="2019-01", end="2026-06", freq="M").strftime("%Y-%m"))
    assert obs_months == expected_months
    assert len(obs_months) == 90


def test_exceptions_reporting(processed_data_dir):
    exc_path = os.path.join(processed_data_dir, "data_quality_exceptions.csv")
    assert os.path.exists(exc_path)
    df_exc = pd.read_csv(exc_path)
    # Priority Sector (Memo) has 90 placeholder missing rows that were quarantined
    assert len(df_exc) >= 90
    assert (df_exc["review_status"] == "open").all()
