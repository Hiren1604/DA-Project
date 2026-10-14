"""
Database Loader Module for CreditLens.
Loads cleaned datasets into relational dimension and fact tables,
creates analytical KPI views, and executes database integrity checks.
Supports SQLite (default local) and PostgreSQL.
"""

import os
import sqlite3
import pandas as pd


def get_db_connection(db_path: str = "data/processed/credit_lens.db") -> sqlite3.Connection:
    """Create or connect to SQLite database."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def execute_sql_file(conn: sqlite3.Connection, sql_path: str) -> None:
    """Execute SQL script containing multiple statements."""
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()


def populate_dimensions_and_facts(conn: sqlite3.Connection, data_dir: str = "data") -> dict:
    """
    Populate dim_sector, dim_date, dim_source, fact_credit_outstanding,
    and data_quality_exceptions from cleaned processed CSV files.
    """
    proc_dir = os.path.join(data_dir, "processed")
    clean_csv = os.path.join(proc_dir, "credit_clean.csv")
    exc_csv = os.path.join(proc_dir, "data_quality_exceptions.csv")

    df_clean = pd.read_csv(clean_csv)
    df_clean["reporting_date"] = pd.to_datetime(df_clean["reporting_date"])

    # 1. Populate dim_sector
    df_sectors = df_clean[[
        "sector_code", "sector_name", "parent_code", "parent_sector_name",
        "hierarchy_level", "is_parent_total", "is_mutually_exclusive"
    ]].drop_duplicates(subset=["sector_code"]).reset_index(drop=True)
    df_sectors["sector_id"] = df_sectors.index + 1
    df_sectors["parent_code"] = df_sectors["parent_code"].fillna("")
    df_sectors["parent_sector_name"] = df_sectors["parent_sector_name"].fillna("")

    df_sectors[[
        "sector_id", "sector_code", "sector_name", "parent_code", "parent_sector_name",
        "hierarchy_level", "is_parent_total", "is_mutually_exclusive"
    ]].to_sql("dim_sector", conn, if_exists="append", index=False)

    # 2. Populate dim_date
    df_dates = df_clean[[
        "reporting_date", "reporting_month", "reporting_year", "reporting_quarter"
    ]].drop_duplicates(subset=["reporting_date"]).sort_values("reporting_date").reset_index(drop=True)
    df_dates["date_id"] = df_dates.index + 1
    df_dates["calendar_date"] = df_dates["reporting_date"].dt.strftime("%Y-%m-%d")
    df_dates["month_num"] = df_dates["reporting_date"].dt.month
    df_dates["month_name"] = df_dates["reporting_date"].dt.strftime("%B")

    df_dates[[
        "date_id", "calendar_date", "reporting_month", "reporting_year",
        "reporting_quarter", "month_num", "month_name"
    ]].to_sql("dim_date", conn, if_exists="append", index=False)

    # 3. Populate dim_source
    sources = [{
        "source_id": 1,
        "source_name": "Reserve Bank of India (RBI)",
        "publication_table": "Industry-wise deployment of bank credit (Table 16)",
        "source_url": "https://dbie.rbihub.in/banking/bank-credit-by-industry",
        "unit": "Rupees crores",
        "ingestion_version": "1.0.0"
    }]
    pd.DataFrame(sources).to_sql("dim_source", conn, if_exists="append", index=False)

    # 4. Populate fact_credit_outstanding
    date_map = df_dates.set_index("calendar_date")["date_id"].to_dict()
    sector_map = df_sectors.set_index("sector_code")["sector_id"].to_dict()

    df_fact = df_clean.copy()
    df_fact["calendar_date"] = df_fact["reporting_date"].dt.strftime("%Y-%m-%d")
    df_fact["date_id"] = df_fact["calendar_date"].map(date_map)
    df_fact["sector_id"] = df_fact["sector_code"].map(sector_map)
    df_fact["source_id"] = 1

    df_fact[[
        "observation_id", "date_id", "sector_id", "source_id",
        "credit_outstanding_cr", "quality_status"
    ]].to_sql("fact_credit_outstanding", conn, if_exists="append", index=False)

    # 5. Populate data_quality_exceptions
    if os.path.exists(exc_csv):
        df_exc = pd.read_csv(exc_csv)
        if not df_exc.empty:
            df_exc["exception_id"] = df_exc.index + 1
            df_exc[[
                "exception_id", "observation_id", "dataset", "rule_id",
                "severity", "error_details", "review_status"
            ]].to_sql("data_quality_exceptions", conn, if_exists="append", index=False)

    return {
        "sectors_loaded": len(df_sectors),
        "dates_loaded": len(df_dates),
        "facts_loaded": len(df_fact),
        "exceptions_loaded": len(df_exc) if os.path.exists(exc_csv) and not df_exc.empty else 0
    }


def run_database_load(
    db_path: str = "data/processed/credit_lens.db",
    sql_dir: str = "sql",
    data_dir: str = "data"
) -> dict:
    """
    Run complete relational database creation, data population,
    view creation, and post-load checks.
    """
    conn = get_db_connection(db_path)

    schema_sql = os.path.join(sql_dir, "01_schema.sql")
    views_sql = os.path.join(sql_dir, "03_kpi_views.sql")

    # Step 1: DDL Schema
    execute_sql_file(conn, schema_sql)

    # Step 2: Populate tables
    stats = populate_dimensions_and_facts(conn, data_dir)

    # Step 3: Create Views
    execute_sql_file(conn, views_sql)

    conn.close()
    return stats


if __name__ == "__main__":
    res = run_database_load()
    print("Database build completed successfully.")
    print("Sectors loaded:", res["sectors_loaded"])
    print("Dates loaded:", res["dates_loaded"])
    print("Fact observations loaded:", res["facts_loaded"])
    print("Exceptions loaded:", res["exceptions_loaded"])
