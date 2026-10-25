"""
Data Validation and Quality Assurance Module for CreditLens.
Performs deterministic data-quality checks on cleaned observations,
evaluates hierarchy consistency, checks uniqueness, and produces data quality reports.
"""

import os
import pandas as pd
import numpy as np


def validate_dataset(df: pd.DataFrame, dataset_name: str = "Industry Credit") -> tuple[list[dict], pd.DataFrame]:
    """
    Execute rigorous validation rules on cleaned DataFrame.
    Returns a list of validation check summaries and a DataFrame of exception records.
    """
    checks = []
    exceptions = []

    df = df.copy()
    df["reporting_date"] = pd.to_datetime(df["reporting_date"], errors="coerce")
    total_records = len(df)

    # 1. Null / Invalid Date Check
    invalid_dates = df[df["reporting_date"].isna()]
    checks.append({
        "dataset": dataset_name,
        "rule_id": "VR-01",
        "rule_name": "Date Validity",
        "description": "Reporting dates must be valid, non-null timestamps",
        "records_evaluated": total_records,
        "exceptions_count": len(invalid_dates),
        "status": "PASS" if len(invalid_dates) == 0 else "FAIL",
        "severity": "CRITICAL"
    })
    for _, row in invalid_dates.iterrows():
        exceptions.append({
            "observation_id": row["observation_id"],
            "dataset": dataset_name,
            "rule_id": "VR-01",
            "severity": "CRITICAL",
            "error_details": "Unparseable or null reporting date",
            "review_status": "open"
        })

    # 2. Missing Amount Check
    missing_amounts = df[df["credit_outstanding_cr"].isna()]
    checks.append({
        "dataset": dataset_name,
        "rule_id": "VR-02",
        "rule_name": "Numeric Completeness",
        "description": "Credit outstanding must have a non-null numeric value",
        "records_evaluated": total_records,
        "exceptions_count": len(missing_amounts),
        "status": "PASS" if len(missing_amounts) == 0 else ("WARNING" if dataset_name == "Major Sectors" else "FAIL"),
        "severity": "MEDIUM" if dataset_name == "Major Sectors" and len(missing_amounts) else "HIGH"
    })
    for _, row in missing_amounts.iterrows():
        exceptions.append({
            "observation_id": row["observation_id"],
            "dataset": dataset_name,
            "rule_id": "VR-02",
            "severity": "HIGH",
            "error_details": f"Missing credit amount for sector {row['sector_code']} on {row['reporting_date']}",
            "review_status": "open"
        })

    # 3. Non-Negative Amount Check
    negative_amounts = df[df["credit_outstanding_cr"] < 0]
    checks.append({
        "dataset": dataset_name,
        "rule_id": "VR-03",
        "rule_name": "Non-Negative Values",
        "description": "Credit outstanding must not be negative",
        "records_evaluated": total_records,
        "exceptions_count": len(negative_amounts),
        "status": "PASS" if len(negative_amounts) == 0 else "FAIL",
        "severity": "HIGH"
    })
    for _, row in negative_amounts.iterrows():
        exceptions.append({
            "observation_id": row["observation_id"],
            "dataset": dataset_name,
            "rule_id": "VR-03",
            "severity": "HIGH",
            "error_details": f"Negative credit amount ({row['credit_outstanding_cr']}) for sector {row['sector_code']}",
            "review_status": "open"
        })

    # 4. Uniqueness Check on Natural Key (reporting_date, sector_code)
    duplicate_mask = df.duplicated(subset=["reporting_date", "sector_code"], keep=False)
    duplicate_records = df[duplicate_mask]
    checks.append({
        "dataset": dataset_name,
        "rule_id": "VR-04",
        "rule_name": "Natural Key Uniqueness",
        "description": "Combination of reporting_date and sector_code must be unique",
        "records_evaluated": total_records,
        "exceptions_count": len(duplicate_records),
        "status": "PASS" if len(duplicate_records) == 0 else "FAIL",
        "severity": "CRITICAL"
    })
    for _, row in duplicate_records.iterrows():
        exceptions.append({
            "observation_id": row["observation_id"],
            "dataset": dataset_name,
            "rule_id": "VR-04",
            "severity": "CRITICAL",
            "error_details": f"Duplicate natural key (date={row['reporting_date']}, sector={row['sector_code']})",
            "review_status": "open"
        })

    # 5. Continuous Monthly Series Check
    obs_months = set(df["reporting_month"].unique())
    min_month = df["reporting_month"].min()
    max_month = df["reporting_month"].max()
    expected_period_range = pd.period_range(start=min_month, end=max_month, freq="M").strftime("%Y-%m")
    missing_months = set(expected_period_range) - obs_months
    checks.append({
        "dataset": dataset_name,
        "rule_id": "VR-05",
        "rule_name": "Time-Series Continuity",
        "description": "Reporting periods must span consecutive calendar months without historical gaps",
        "records_evaluated": len(expected_period_range),
        "exceptions_count": len(missing_months),
        "status": "PASS" if len(missing_months) == 0 else "WARNING",
        "severity": "MEDIUM"
    })
    for m in missing_months:
        exceptions.append({
            "observation_id": 0,
            "dataset": dataset_name,
            "rule_id": "VR-05",
            "severity": "MEDIUM",
            "error_details": f"Historical reporting gap: missing month {m}",
            "review_status": "open"
        })

    # 6. Hierarchy Sum Consistency Check (for Table 16 Industry Credit)
    if dataset_name == "Industry Credit":
        level_1_codes = [f"2.{i}" for i in range(1, 20)]
        grand_total_rows = df[df["sector_code"] == "2"].set_index("reporting_date")["credit_outstanding_cr"]
        level_1_sum = df[df["sector_code"].isin(level_1_codes)].groupby("reporting_date")["credit_outstanding_cr"].sum()

        reconciliation_diff = (grand_total_rows - level_1_sum).abs()
        max_diff = reconciliation_diff.max()
        # Rounding tolerance of 2.5 Cr (since 19 individual sectors rounded to 2 decimals)
        hierarchy_fails = reconciliation_diff[reconciliation_diff > 2.5]
        checks.append({
            "dataset": dataset_name,
            "rule_id": "VR-06",
            "rule_name": "Hierarchy Aggregation Integrity",
            "description": "Sum of 19 Level-1 sectors (2.1 to 2.19) must match Grand Total (code 2) within rounding tolerance",
            "records_evaluated": len(grand_total_rows),
            "exceptions_count": len(hierarchy_fails),
            "status": "PASS" if len(hierarchy_fails) == 0 else "FAIL",
            "severity": "HIGH"
        })
        for dt_val, diff_val in hierarchy_fails.items():
            exceptions.append({
                "observation_id": 0,
                "dataset": dataset_name,
                "rule_id": "VR-06",
                "severity": "HIGH",
                "error_details": f"Hierarchy discrepancy of {diff_val:.2f} Cr on {dt_val}",
                "review_status": "open"
            })

    # 7. Complete sector-by-month panel: every observed category must occur each month.
    months = sorted(df["reporting_month"].dropna().astype(str).unique())
    sectors = sorted(df["sector_code"].dropna().astype(str).unique())
    expected = pd.MultiIndex.from_product([months, sectors], names=["reporting_month", "sector_code"])
    observed = pd.MultiIndex.from_frame(
        df[["reporting_month", "sector_code"]].astype(str).drop_duplicates()
    )
    missing_keys = expected.difference(observed)
    checks.append({
        "dataset": dataset_name,
        "rule_id": "VR-07",
        "rule_name": "Sector-Month Panel Completeness",
        "description": "Every observed sector code must have a record in every reporting month",
        "records_evaluated": len(expected),
        "exceptions_count": len(missing_keys),
        "status": "PASS" if len(missing_keys) == 0 else "FAIL",
        "severity": "HIGH"
    })
    for month, code in missing_keys:
        exceptions.append({
            "observation_id": 0,
            "dataset": dataset_name,
            "rule_id": "VR-07",
            "severity": "HIGH",
            "error_details": f"Missing sector-month record: sector {code}, month {month}",
            "review_status": "open"
        })

    df_exceptions = pd.DataFrame(exceptions)
    if df_exceptions.empty:
        df_exceptions = pd.DataFrame(columns=[
            "observation_id", "dataset", "rule_id", "severity", "error_details", "review_status"
        ])

    return checks, df_exceptions


def run_validation(data_dir: str = "data") -> pd.DataFrame:
    """
    Run validation on cleaned datasets and write data_quality_report.csv and exceptions table.
    """
    proc_dir = os.path.join(data_dir, "processed")
    t16_clean_path = os.path.join(proc_dir, "credit_clean.csv")
    t15_clean_path = os.path.join(proc_dir, "major_sectors_clean.csv")

    df_t16 = pd.read_csv(t16_clean_path)
    df_t15 = pd.read_csv(t15_clean_path)

    checks_t16, exc_t16 = validate_dataset(df_t16, "Industry Credit")
    checks_t15, exc_t15 = validate_dataset(df_t15, "Major Sectors")

    all_checks = checks_t16 + checks_t15
    df_checks = pd.DataFrame(all_checks)

    all_exceptions = pd.concat([exc_t16, exc_t15], ignore_index=True)

    report_path = os.path.join(proc_dir, "data_quality_report.csv")
    df_checks.to_csv(report_path, index=False, encoding="utf-8")

    exceptions_path = os.path.join(proc_dir, "data_quality_exceptions.csv")
    all_exceptions.to_csv(exceptions_path, index=False, encoding="utf-8")

    return df_checks


if __name__ == "__main__":
    report = run_validation()
    print("Validation completed.")
    print(report[["dataset", "rule_id", "rule_name", "status", "exceptions_count"]].to_string(index=False))
