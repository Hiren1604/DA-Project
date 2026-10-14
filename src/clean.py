"""
Data Cleaning and Normalization Module for CreditLens.
Standardizes dates, industry category hierarchies, labels, and quality flags.
"""

import os
import re
import pandas as pd
import numpy as np


def clean_label(label: str) -> str:
    """Strip superscripts, footnotes, and redundant whitespace from labels."""
    if not isinstance(label, str):
        return ""
    # Remove superscripts 1-9
    cleaned = re.sub(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]", "", label)
    # Remove multiple spaces
    cleaned = " ".join(cleaned.strip().split())
    return cleaned


def parse_reporting_date(date_str: str) -> pd.Timestamp:
    """Parse RBI date string e.g. 'January,  18 2019' or 'June,  30 2026'."""
    clean_str = " ".join(date_str.replace(",", " ").split())
    return pd.to_datetime(clean_str, format="%B %d %Y")


def clean_industry_credit(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize RBI Table 16 (Industry-wise Deployment of Bank Credit).
    """
    df = df_raw.copy()

    # Parse dates
    df["reporting_date"] = df["period_raw"].apply(parse_reporting_date)
    df["reporting_month"] = df["reporting_date"].dt.strftime("%Y-%m")
    df["reporting_year"] = df["reporting_date"].dt.year
    df["reporting_quarter"] = df["reporting_date"].dt.to_period("Q").astype(str)

    # Clean label
    df["sector_name"] = df["item_label"].apply(clean_label)
    df["sector_code"] = df["item_code"].astype(str)
    df["parent_code"] = df["parent_code"].fillna("").astype(str)

    # Numeric credit outstanding
    df["credit_outstanding_cr"] = pd.to_numeric(df["amount_cr"], errors="coerce")

    # Hierarchy classification
    # Code '2' is Grand Total
    # Code '2.x' (where x is 1..19) is Level 1 major industry
    # Code '2.x.y' is Level 2 sub-industry
    def get_hierarchy_level(code: str) -> str:
        if code == "2":
            return "grand_total"
        parts = code.split(".")
        if len(parts) == 2:
            return "sector_total"
        elif len(parts) >= 3:
            return "sub_sector"
        return "other"

    df["hierarchy_level"] = df["sector_code"].apply(get_hierarchy_level)

    # Parent sectors map
    # Find which codes act as parents
    parent_codes = set(df["parent_code"].unique()) - {""}
    df["is_parent_total"] = df["sector_code"].isin(parent_codes) | (df["sector_code"] == "2")

    # Mutually exclusive sectors for portfolio analysis: exactly the 19 Level 1 sectors
    level_1_codes = {f"2.{i}" for i in range(1, 20)}
    df["is_mutually_exclusive"] = df["sector_code"].isin(level_1_codes)

    # Lookup parent name
    code_to_name = df[["sector_code", "sector_name"]].drop_duplicates().set_index("sector_code")["sector_name"].to_dict()
    df["parent_sector_name"] = df["parent_code"].map(code_to_name).fillna("")

    # Quality status and validation flags
    df["quality_status"] = "valid"
    df["exception_reason"] = ""

    # Flag missing amount
    missing_mask = df["credit_outstanding_cr"].isna()
    df.loc[missing_mask, "quality_status"] = "review"
    df.loc[missing_mask, "exception_reason"] = "missing_amount"

    # Flag negative amount
    neg_mask = df["credit_outstanding_cr"] < 0
    df.loc[neg_mask, "quality_status"] = "review"
    df.loc[neg_mask, "exception_reason"] = "negative_amount"

    # Sort deterministically
    df = df.sort_values(by=["reporting_date", "sector_code"]).reset_index(drop=True)
    df["observation_id"] = df.index + 1

    cols = [
        "observation_id",
        "reporting_date",
        "reporting_month",
        "reporting_year",
        "reporting_quarter",
        "sector_code",
        "sector_name",
        "parent_code",
        "parent_sector_name",
        "hierarchy_level",
        "is_parent_total",
        "is_mutually_exclusive",
        "credit_outstanding_cr",
        "unit",
        "quality_status",
        "exception_reason"
    ]
    return df[cols]


def clean_major_sectors(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize RBI Table 15 (Deployment of Gross Bank Credit by Major Sectors).
    """
    df = df_raw.copy()

    df["reporting_date"] = df["period_raw"].apply(parse_reporting_date)
    df["reporting_month"] = df["reporting_date"].dt.strftime("%Y-%m")
    df["reporting_year"] = df["reporting_date"].dt.year
    df["reporting_quarter"] = df["reporting_date"].dt.to_period("Q").astype(str)

    df["sector_name"] = df["item_label"].apply(clean_label)
    df["sector_code"] = df["item_code"].astype(str)
    df["parent_code"] = df["parent_code"].fillna("").astype(str)
    df["credit_outstanding_cr"] = pd.to_numeric(df["amount_cr"], errors="coerce")

    def get_major_hierarchy(code: str) -> str:
        if code in ["I", "II", "III"]:
            return "grand_total"
        parts = code.split(".")
        if len(parts) == 1:
            return "major_sector"
        return "sub_sector"

    df["hierarchy_level"] = df["sector_code"].apply(get_major_hierarchy)
    parent_codes = set(df["parent_code"].unique()) - {""}
    df["is_parent_total"] = df["sector_code"].isin(parent_codes) | df["sector_code"].isin(["I", "II", "III"])

    code_to_name = df[["sector_code", "sector_name"]].drop_duplicates().set_index("sector_code")["sector_name"].to_dict()
    df["parent_sector_name"] = df["parent_code"].map(code_to_name).fillna("")

    df["quality_status"] = "valid"
    df["exception_reason"] = ""

    missing_mask = df["credit_outstanding_cr"].isna()
    df.loc[missing_mask, "quality_status"] = "review"
    df.loc[missing_mask, "exception_reason"] = "missing_amount"

    neg_mask = df["credit_outstanding_cr"] < 0
    df.loc[neg_mask, "quality_status"] = "review"
    df.loc[neg_mask, "exception_reason"] = "negative_amount"

    df = df.sort_values(by=["reporting_date", "sector_code"]).reset_index(drop=True)
    df["observation_id"] = df.index + 1

    cols = [
        "observation_id",
        "reporting_date",
        "reporting_month",
        "reporting_year",
        "reporting_quarter",
        "sector_code",
        "sector_name",
        "parent_code",
        "parent_sector_name",
        "hierarchy_level",
        "is_parent_total",
        "credit_outstanding_cr",
        "unit",
        "quality_status",
        "exception_reason"
    ]
    return df[cols]


def run_cleaning(data_dir: str = "data") -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Execute data cleaning on raw CSVs and save to data/processed.
    """
    raw_dir = os.path.join(data_dir, "raw")
    proc_dir = os.path.join(data_dir, "processed")
    os.makedirs(proc_dir, exist_ok=True)

    t16_raw_path = os.path.join(raw_dir, "rbi_industry_credit_long_raw.csv")
    t15_raw_path = os.path.join(raw_dir, "rbi_major_sectors_long_raw.csv")

    df_t16_raw = pd.read_csv(t16_raw_path)
    df_t16_clean = clean_industry_credit(df_t16_raw)
    t16_clean_path = os.path.join(proc_dir, "credit_clean.csv")
    df_t16_clean.to_csv(t16_clean_path, index=False, encoding="utf-8")

    df_t15_raw = pd.read_csv(t15_raw_path)
    df_t15_clean = clean_major_sectors(df_t15_raw)
    t15_clean_path = os.path.join(proc_dir, "major_sectors_clean.csv")
    df_t15_clean.to_csv(t15_clean_path, index=False, encoding="utf-8")

    return df_t16_clean, df_t15_clean


if __name__ == "__main__":
    c1, c2 = run_cleaning()
    print("Cleaning completed successfully.")
    print("Cleaned Industry Credit rows:", len(c1))
    print("Cleaned Major Sectors rows:", len(c2))
