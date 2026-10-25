"""
Data Ingestion Module for CreditLens.
Acquires and archives raw statistical releases from Reserve Bank of India (RBI) DBIE,
records cryptographic hashes, and creates standardized long-format raw datasets.
"""

import os
import json
import hashlib
import shutil
from datetime import datetime, timezone
import pandas as pd


def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def unpivot_rbi_json(data: dict, dataset_type: str = "industry") -> pd.DataFrame:
    """
    Transform nested RBI DBIE JSON structure into tabular long-format DataFrame.
    """
    periods = data.get("periods", [])
    items = data.get("items", [])
    unit = data.get("unit", "Rupees crores")

    rows = []
    for item in items:
        code = item.get("code")
        parent = item.get("parent")
        label = item.get("label", "").strip()
        values = item.get("values", [])

        for idx, period_str in enumerate(periods):
            val = values[idx] if idx < len(values) else None
            rows.append({
                "period_raw": period_str,
                "item_code": code,
                "parent_code": parent,
                "item_label": label,
                "amount_cr": val,
                "unit": unit,
                "dataset_type": dataset_type
            })

    return pd.DataFrame(rows)


def run_ingestion(
    data_dir: str = "data",
    scratch_table16: str | None = None,
    scratch_table15: str | None = None
) -> dict:
    """
    Run full ingestion pipeline: copy/archive raw JSON, compute hashes, save source metadata,
    and generate unpivoted raw CSV files.
    """
    raw_dir = os.path.join(data_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    dest_t16 = os.path.join(raw_dir, "rbi_industry_credit_raw.json")
    dest_t15 = os.path.join(raw_dir, "rbi_sector_credit_raw.json")

    # Load Table 16
    if scratch_table16 and os.path.exists(scratch_table16):
        shutil.copyfile(scratch_table16, dest_t16)
        with open(dest_t16, "r", encoding="utf-8") as f:
            data_t16 = json.load(f)
    elif os.path.exists(dest_t16):
        with open(dest_t16, "r", encoding="utf-8") as f:
            data_t16 = json.load(f)
    else:
        raise FileNotFoundError("Raw Table 16 data not found.")


    # Load Table 15
    if scratch_table15 and os.path.exists(scratch_table15):
        shutil.copyfile(scratch_table15, dest_t15)
        with open(dest_t15, "r", encoding="utf-8") as f:
            data_t15 = json.load(f)
    elif os.path.exists(dest_t15):
        with open(dest_t15, "r", encoding="utf-8") as f:
            data_t15 = json.load(f)
    else:
        raise FileNotFoundError("Raw Table 15 data not found.")


    # Compute hashes
    hash_t16 = compute_sha256(dest_t16)
    hash_t15 = compute_sha256(dest_t15)

    # Unpivot to long format
    df_t16_long = unpivot_rbi_json(data_t16, dataset_type="industry")
    t16_csv_path = os.path.join(raw_dir, "rbi_industry_credit_long_raw.csv")
    df_t16_long.to_csv(t16_csv_path, index=False, encoding="utf-8")

    df_t15_long = unpivot_rbi_json(data_t15, dataset_type="major_sector")
    t15_csv_path = os.path.join(raw_dir, "rbi_major_sectors_long_raw.csv")
    df_t15_long.to_csv(t15_csv_path, index=False, encoding="utf-8")

    # Source metadata
    meta = {
        "project": "CreditLens - Indian Banking & Credit Portfolio Analytics",
        "publisher": "Reserve Bank of India (RBI)",
        "source_portal": "Database on Indian Economy (DBIE)",
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_mode": "external_file_import" if scratch_table16 or scratch_table15 else "bundled_archive",
        "ingestion_version": "1.0.0",
        "modules": {
            "module_a_industry_credit": {
                "title": data_t16.get("reportTitle", "Industry-wise deployment of bank credit (Table 16)"),
                "source_url": "https://dbie.rbihub.in/banking/bank-credit-by-industry",
                "raw_file": "data/raw/rbi_industry_credit_raw.json",
                "sha256": hash_t16,
                "periods_count": len(data_t16.get("periods", [])),
                "items_count": len(data_t16.get("items", [])),
                "total_observations": len(df_t16_long),
                "reporting_min": data_t16.get("periods", [])[0],
                "reporting_max": data_t16.get("periods", [])[-1],
                "unit": data_t16.get("unit", "Rupees crores")
            },
            "module_b_major_sectors": {
                "title": data_t15.get("reportTitle", "Deployment of gross bank credit by major sectors (Table 15)"),
                "source_url": "https://dbie.rbihub.in/banking/bank-credit-by-sector",
                "raw_file": "data/raw/rbi_sector_credit_raw.json",
                "sha256": hash_t15,
                "periods_count": len(data_t15.get("periods", [])),
                "items_count": len(data_t15.get("items", [])),
                "total_observations": len(df_t15_long),
                "reporting_min": data_t15.get("periods", [])[0],
                "reporting_max": data_t15.get("periods", [])[-1],
                "unit": data_t15.get("unit", "Rupees crores")
            }
        },
        "known_comparability_breaks": [
            {
                "date": "2019-01",
                "description": "Sectoral credit data based on revised reporting format; earlier published component values underwent changes."
            },
            {
                "date": "2023-07-28",
                "description": "Data since July 28, 2023 include the impact of the merger of a non-bank (HDFC Ltd.) with a bank (HDFC Bank), causing a structural upward shift in credit series."
            }
        ]
    }

    meta_path = os.path.join(raw_dir, "source_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return meta


if __name__ == "__main__":
    result = run_ingestion()
    print("Ingestion completed successfully.")
    print("Table 16 observations:", result["modules"]["module_a_industry_credit"]["total_observations"])
    print("Table 15 observations:", result["modules"]["module_b_major_sectors"]["total_observations"])
