"""
CreditLens FastAPI REST API Layer.
Serves validated credit KPIs, sector hierarchy, time-series trends,
and data quality summaries directly from the SQLite database.
"""

import os
import sqlite3
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse

app = FastAPI(
    title="CreditLens API",
    description="Validated Indian Banking & Credit Portfolio Analytics REST API",
    version="1.0.0"
)

DB_PATH = os.environ.get("DATABASE_URL", "data/processed/credit_lens.db").replace("sqlite:///", "")


def get_db():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database not found. Please run pipeline first.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


STATIC_INDEX = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "index.html")


@app.get("/", response_class=FileResponse)
def serve_dashboard():
    """Serves the interactive CreditLens web dashboard."""
    if os.path.exists(STATIC_INDEX):
        return FileResponse(STATIC_INDEX)
    return HTMLResponse("<h1>CreditLens API is Running.</h1><p>Visit <a href='/docs'>/docs</a> for API specifications.</p>")


@app.get("/api/metadata")
def get_metadata():
    """Returns source metadata, publication version, and reporting bounds."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dim_source LIMIT 1")
    source = dict(cursor.fetchone())

    cursor.execute("SELECT MIN(calendar_date) as min_date, MAX(calendar_date) as max_date, COUNT(DISTINCT reporting_month) as total_months FROM dim_date")
    dates = dict(cursor.fetchone())
    conn.close()

    return {
        "project": "CreditLens — Indian Banking & Credit Portfolio Analytics",
        "version": "1.0.0",
        "source": source,
        "reporting_bounds": dates
    }


@app.get("/api/summary")
def get_summary(month: Optional[str] = Query(None, description="Reporting month (YYYY-MM). Defaults to latest.")):
    """Returns high-level KPI cards for executive overview."""
    conn = get_db()
    cursor = conn.cursor()

    if not month:
        cursor.execute("SELECT MAX(reporting_month) FROM dim_date")
        month = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM v_total_industry_monthly WHERE reporting_month = ?", (month,))
    row_tot = cursor.fetchone()
    if not row_tot:
        conn.close()
        raise HTTPException(status_code=404, detail=f"No data for period {month}")

    tot_dict = dict(row_tot)

    cursor.execute("SELECT * FROM v_industry_concentration_hhi WHERE reporting_month = ?", (month,))
    conc_row = cursor.fetchone()
    conc_dict = dict(conc_row) if conc_row else {}

    conn.close()
    return {
        "reporting_month": month,
        "total_credit_cr": tot_dict.get("total_credit_cr"),
        "mom_growth_pct": tot_dict.get("mom_growth_pct"),
        "yoy_growth_pct": tot_dict.get("yoy_growth_pct"),
        "mom_change_cr": tot_dict.get("mom_change_cr"),
        "yoy_change_cr": tot_dict.get("yoy_change_cr"),
        "hhi_index": conc_dict.get("hhi_index"),
        "top3_concentration_share_pct": conc_dict.get("top3_concentration_share_pct"),
        "largest_sector": conc_dict.get("largest_sector"),
        "largest_sector_share_pct": conc_dict.get("largest_sector_share_pct")
    }


@app.get("/api/sectors")
def get_sectors(level: Optional[str] = Query(None, description="Hierarchy level: grand_total, sector_total, sub_sector")):
    """Returns sector hierarchy taxonomy."""
    conn = get_db()
    cursor = conn.cursor()
    if level:
        cursor.execute("SELECT * FROM dim_sector WHERE hierarchy_level = ? ORDER BY sector_code", (level,))
    else:
        cursor.execute("SELECT * FROM dim_sector ORDER BY sector_code")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"count": len(rows), "sectors": rows}


@app.get("/api/credit/trends")
def get_credit_trends(sector_code: Optional[str] = Query("2", description="Sector code. Defaults to 2 (Total Industries)")):
    """Returns monthly credit trend series for a specified sector."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reporting_month, calendar_date, credit_outstanding_cr, sector_share_pct, mom_growth_pct, yoy_growth_pct
        FROM v_sector_monthly_kpis
        WHERE sector_code = ?
        ORDER BY reporting_month ASC
    """, (sector_code,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for sector_code {sector_code}")
    return {"sector_code": sector_code, "count": len(rows), "series": rows}


@app.get("/api/credit/comparison")
def get_credit_comparison(month: Optional[str] = Query(None, description="Reporting month (YYYY-MM). Defaults to latest.")):
    """Returns ranking and comparison of all 19 mutually exclusive sectors for a given period."""
    conn = get_db()
    cursor = conn.cursor()
    if not month:
        cursor.execute("SELECT MAX(reporting_month) FROM dim_date")
        month = cursor.fetchone()[0]

    cursor.execute("""
        SELECT sector_code, sector_name, credit_outstanding_cr, sector_share_pct, yoy_growth_pct, mom_growth_pct
        FROM v_sector_monthly_kpis
        WHERE reporting_month = ? AND is_mutually_exclusive = 1
        ORDER BY credit_outstanding_cr DESC
    """, (month,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"reporting_month": month, "count": len(rows), "comparison": rows}


@app.get("/api/data-quality")
def get_data_quality():
    """Returns data quality checks summary and exception counts."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM v_data_quality_summary")
    exceptions = [dict(r) for r in cursor.fetchall()]

    # Read CSV report
    val_report_path = "data/processed/data_quality_report.csv"
    val_checks = []
    if os.path.exists(val_report_path):
        import pandas as pd
        val_checks = pd.read_csv(val_report_path).to_dict(orient="records")

    conn.close()
    return {
        "validation_checks": val_checks,
        "exceptions_summary": exceptions
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
