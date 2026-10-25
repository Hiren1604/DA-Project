"""
CreditLens FastAPI REST API Layer.
Serves validated credit KPIs, sector hierarchy, time-series trends,
and data quality summaries directly from the SQLite database.
"""

import os
import sqlite3
import re
from contextlib import closing
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

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


def validate_month(month: Optional[str], conn: sqlite3.Connection) -> str:
    if month is None:
        row = conn.execute("SELECT MAX(reporting_month) FROM dim_date").fetchone()
        return row[0]
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
        raise HTTPException(status_code=422, detail="month must use YYYY-MM format")
    exists = conn.execute("SELECT 1 FROM dim_date WHERE reporting_month = ? LIMIT 1", (month,)).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail=f"No data for period {month}")
    return month


STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
STATIC_INDEX = os.path.join(STATIC_DIR, "index.html")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


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
    with closing(conn):
        source = dict(conn.execute("SELECT * FROM dim_source LIMIT 1").fetchone())
        dates = dict(conn.execute("SELECT MIN(calendar_date) as min_date, MAX(calendar_date) as max_date, COUNT(DISTINCT reporting_month) as total_months FROM dim_date").fetchone())

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
    with closing(conn):
        month = validate_month(month, conn)
        row_tot = conn.execute("SELECT * FROM v_total_industry_monthly WHERE reporting_month = ?", (month,)).fetchone()
        tot_dict = dict(row_tot)
        conc_row = conn.execute("SELECT * FROM v_industry_concentration_hhi WHERE reporting_month = ?", (month,)).fetchone()
        conc_dict = dict(conc_row) if conc_row else {}
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
    with closing(conn):
        if level:
            rows = [dict(r) for r in conn.execute("SELECT * FROM dim_sector WHERE hierarchy_level = ? ORDER BY sector_code", (level,)).fetchall()]
        else:
            rows = [dict(r) for r in conn.execute("SELECT * FROM dim_sector ORDER BY sector_code").fetchall()]
    return {"count": len(rows), "sectors": rows}


@app.get("/api/credit/trends")
def get_credit_trends(sector_code: Optional[str] = Query("2", description="Sector code. Defaults to 2 (Total Industries)")):
    """Returns monthly credit trend series for a specified sector."""
    conn = get_db()
    with closing(conn):
        rows = [dict(r) for r in conn.execute("""
            SELECT reporting_month, calendar_date, credit_outstanding_cr, sector_share_pct, mom_growth_pct, yoy_growth_pct
            FROM v_sector_monthly_kpis WHERE sector_code = ? ORDER BY reporting_month ASC
        """, (sector_code,)).fetchall()]
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for sector_code {sector_code}")
    return {"sector_code": sector_code, "count": len(rows), "series": rows}


@app.get("/api/credit/comparison")
def get_credit_comparison(month: Optional[str] = Query(None, description="Reporting month (YYYY-MM). Defaults to latest.")):
    """Returns ranking and comparison of all 19 mutually exclusive sectors for a given period."""
    conn = get_db()
    with closing(conn):
        month = validate_month(month, conn)
        rows = [dict(r) for r in conn.execute("""
        SELECT sector_code, sector_name, credit_outstanding_cr, sector_share_pct, yoy_growth_pct, mom_growth_pct
        FROM v_sector_monthly_kpis
        WHERE reporting_month = ? AND is_mutually_exclusive = 1
        ORDER BY credit_outstanding_cr DESC
    """, (month,)).fetchall()]
    return {"reporting_month": month, "count": len(rows), "comparison": rows}


@app.get("/api/credit/concentration")
def get_credit_concentration():
    """Return the computed monthly HHI and concentration series."""
    conn = get_db()
    with closing(conn):
        rows = [dict(r) for r in conn.execute("""
            SELECT reporting_month, total_sectors_evaluated, total_industry_credit_cr,
                   hhi_index, hhi_fraction, top3_concentration_share_pct,
                   largest_sector, largest_sector_share_pct
            FROM v_industry_concentration_hhi
            ORDER BY reporting_month ASC
        """).fetchall()]
    return {"count": len(rows), "series": rows}


@app.get("/api/data-quality")
def get_data_quality():
    """Returns data quality checks summary and exception counts."""
    conn = get_db()
    with closing(conn):
        exceptions = [dict(r) for r in conn.execute("SELECT * FROM v_data_quality_summary").fetchall()]

    # Read CSV report
    val_report_path = "data/processed/data_quality_report.csv"
    val_checks = []
    if os.path.exists(val_report_path):
        import pandas as pd
        val_checks = pd.read_csv(val_report_path).to_dict(orient="records")

    return {
        "validation_checks": val_checks,
        "exceptions_summary": exceptions
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
