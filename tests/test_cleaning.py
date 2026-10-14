"""
Unit tests for data cleaning logic and hierarchy standardization.
"""

import pandas as pd
from src.clean import clean_label, parse_reporting_date, clean_industry_credit


def test_clean_label_strips_footnotes():
    assert clean_label("Wholesale Trade¹") == "Wholesale Trade"
    assert clean_label("NBFCs²") == "NBFCs"
    assert clean_label("Other Services³ ") == "Other Services"
    assert clean_label("Mining   &   Quarrying") == "Mining & Quarrying"


def test_parse_reporting_date():
    dt1 = parse_reporting_date("January,  18 2019")
    assert dt1 == pd.Timestamp("2019-01-18")
    dt2 = parse_reporting_date("June,  30 2026")
    assert dt2 == pd.Timestamp("2026-06-30")


def test_hierarchy_assignment(clean_industry_df):
    grand_total = clean_industry_df[clean_industry_df["sector_code"] == "2"]
    assert (grand_total["hierarchy_level"] == "grand_total").all()

    level_1 = clean_industry_df[clean_industry_df["sector_code"] == "2.1"]
    assert (level_1["hierarchy_level"] == "sector_total").all()

    sub_sec = clean_industry_df[clean_industry_df["sector_code"] == "2.2.1"]
    assert (sub_sec["hierarchy_level"] == "sub_sector").all()


def test_mutually_exclusive_count(clean_industry_df):
    unique_sectors = clean_industry_df[["sector_code", "is_mutually_exclusive"]].drop_duplicates()
    mutually_exclusive = unique_sectors[unique_sectors["is_mutually_exclusive"] == True]
    assert len(mutually_exclusive) == 19
    expected_codes = {f"2.{i}" for i in range(1, 20)}
    assert set(mutually_exclusive["sector_code"]) == expected_codes


def test_valid_amounts_nonnegative(clean_industry_df):
    valid_records = clean_industry_df[clean_industry_df["quality_status"] == "valid"]
    assert (valid_records["credit_outstanding_cr"] >= 0).all()
    assert not valid_records["credit_outstanding_cr"].isna().any()
