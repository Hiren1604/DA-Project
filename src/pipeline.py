"""
CreditLens End-to-End Pipeline Orchestrator.
Executes the full pipeline: Ingestion -> Cleaning -> Validation -> Transformations -> Database Loading.
Entry point: python -m src.pipeline
"""

import time
import argparse
from src.ingest import run_ingestion
from src.clean import run_cleaning
from src.validate import run_validation
from src.transform import run_transformations
from src.load import run_database_load


def run_pipeline(data_dir: str = "data", db_path: str = "data/processed/credit_lens.db") -> dict:
    """
    Execute end-to-end analytics workflow.
    """
    start_time = time.time()
    print("=" * 70)
    print("CREDITLENS: INDIAN BANKING & CREDIT PORTFOLIO ANALYTICS PIPELINE")
    print("=" * 70)

    # 1. Ingestion
    print("\n[Step 1/5] Ingesting RBI DBIE statistical tables...")
    t0 = time.time()
    meta = run_ingestion(data_dir=data_dir)
    t16_obs = meta["modules"]["module_a_industry_credit"]["total_observations"]
    t15_obs = meta["modules"]["module_b_major_sectors"]["total_observations"]
    print(f" -> Ingestion complete ({time.time() - t0:.2f}s): {t16_obs} Industry + {t15_obs} Sector records archived.")

    # 2. Cleaning & Normalization
    print("\n[Step 2/5] Cleaning, hierarchy normalization, and date parsing...")
    t0 = time.time()
    df_clean, df_major = run_cleaning(data_dir=data_dir)
    print(f" -> Cleaning complete ({time.time() - t0:.2f}s): {len(df_clean)} Industry and {len(df_major)} Major Sector clean records.")

    # 3. Validation & QA Reporting
    print("\n[Step 3/5] Executing automated data quality assertions...")
    t0 = time.time()
    val_report = run_validation(data_dir=data_dir)
    total_checks = len(val_report)
    passed_checks = len(val_report[val_report["status"] == "PASS"])
    print(f" -> Validation complete ({time.time() - t0:.2f}s): {passed_checks}/{total_checks} rule checks PASSED.")

    # 4. Metric Transformations & Derived KPIs
    print("\n[Step 4/5] Computing MoM/YoY growth, portfolio shares, and HHI concentration...")
    t0 = time.time()
    df_metrics, df_conc = run_transformations(data_dir=data_dir)
    latest_month = df_conc.iloc[-1]
    print(f" -> Transformations complete ({time.time() - t0:.2f}s): {len(df_metrics)} metric records generated.")
    print(f"    Latest Period ({latest_month['reporting_month']}): HHI = {latest_month['hhi_index']}, Top 3 Share = {latest_month['top3_concentration_share_pct']}%")

    # 5. Relational Database Loading & SQL Views
    print("\n[Step 5/5] Building relational schema and compiling SQL KPI views...")
    t0 = time.time()
    db_stats = run_database_load(db_path=db_path, data_dir=data_dir)
    print(f" -> Database build complete ({time.time() - t0:.2f}s): SQLite database loaded at {db_path}.")
    print(f"    Dimensions: {db_stats['sectors_loaded']} sectors, {db_stats['dates_loaded']} dates | Facts: {db_stats['facts_loaded']} records.")

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"SUCCESS: Pipeline executed in {elapsed:.2f} seconds.")
    print("All processed datasets, SQL views, and quality reports are ready.")
    print("=" * 70)

    return {
        "status": "success",
        "elapsed_seconds": elapsed,
        "industry_records": len(df_clean),
        "major_sector_records": len(df_major),
        "database_facts": db_stats["facts_loaded"]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CreditLens Pipeline Runner")
    parser.add_argument("--data-dir", default="data", help="Data directory path")
    parser.add_argument("--db-path", default="data/processed/credit_lens.db", help="SQLite database path")
    args = parser.parse_args()

    run_pipeline(data_dir=args.data_dir, db_path=args.db_path)
