"""
Generator script for excel/kpi_reconciliation.xlsx
Builds a multi-tab professional financial reconciliation workbook using openpyxl,
cross-verifying Python, SQL, and Excel formula outputs for CreditLens KPIs.
"""

import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import sqlite3


def reconciliation_status(values: list[float | None], tolerance: float = 0.01) -> str:
    """Compare independent results; return MISMATCH if any required value differs."""
    if not values or any(value is None for value in values):
        return "INCOMPLETE"
    return "MATCH" if max(values) - min(values) < tolerance else "MISMATCH"


def generate_excel_reconciliation(data_dir: str = "data", output_path: str = "excel/kpi_reconciliation.xlsx"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb = openpyxl.Workbook()
    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    wb.calculation.calcMode = "auto"
    # Remove default sheet
    wb.remove(wb.active)

    # Styles
    navy_fill = PatternFill(start_color="101C30", end_color="101C30", fill_type="solid")
    slate_fill = PatternFill(start_color="233B59", end_color="233B59", fill_type="solid")
    header_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
    pass_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    
    white_title_font = Font(name="Segoe UI", size=14, bold=True, color="FFFFFF")
    white_sub_font = Font(name="Segoe UI", size=10, bold=False, color="CBD5E1")
    header_font = Font(name="Segoe UI", size=10, bold=True, color="1E293B")
    regular_font = Font(name="Segoe UI", size=9)
    bold_font = Font(name="Segoe UI", size=9, bold=True)
    pass_font = Font(name="Segoe UI", size=9, bold=True, color="166534")

    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )

    # -------------------------------------------------------------
    # Tab 1: Executive Summary & Governance
    # -------------------------------------------------------------
    ws1 = wb.create_sheet(title="Executive Summary")
    ws1.views.sheetView[0].showGridLines = True

    # Title block
    ws1.merge_cells("A1:G2")
    ws1["A1"] = "CREDITLENS â€” FINANCIAL KPI RECONCILIATION & AUDIT WORKBOOK"
    ws1["A1"].font = white_title_font
    ws1["A1"].fill = navy_fill
    ws1["A1"].alignment = Alignment(horizontal="center", vertical="center")

    summary_rows = [
        ("Project:", "CreditLens â€” Indian Banking & Credit Portfolio Analytics"),
        ("Primary Source:", "Reserve Bank of India (RBI) â€” DBIE Table 16"),
        ("Historical Coverage:", "January 2019 to June 2026 (90 consecutive reporting months)"),
        ("Reporting Unit:", "Rupees crore (â‚¹ Cr)"),
        ("Audit Grain:", "Sector-by-Month granularity"),
        ("Cross-Tool Scope:", "Independent pandas and SQLite calculations with Excel formula checks"),
        ("Reconciliation Precision:", "0.01 Cr / 0.01% tolerance threshold"),
        ("Audit Result:", "Formula checks recalculate when opened in Excel; inspect comparison status")
    ]

    for idx, (lbl, val) in enumerate(summary_rows, start=4):
        ws1[f"B{idx}"] = lbl
        ws1[f"B{idx}"].font = bold_font
        ws1[f"C{idx}"] = val
        ws1[f"C{idx}"].font = regular_font

    ws1["B13"] = "Eight Documented Credit KPIs Reconciliation Matrix"
    ws1["B13"].font = Font(name="Segoe UI", size=11, bold=True, color="101C30")

    kpi_matrix_headers = ["KPI ID", "Metric Name", "Mathematical Definition", "Python Formula", "SQL View Expression", "Excel Formula", "Status"]
    for col_idx, h in enumerate(kpi_matrix_headers, start=2):
        cell = ws1.cell(row=14, column=col_idx, value=h)
        cell.font = Font(name="Segoe UI", size=9, bold=True, color="FFFFFF")
        cell.fill = slate_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    kpi_matrix_data = [
        ("KPI-01", "Total Industry Credit", "Grand Total observed credit exposure", "df[sector_code=='2']['credit_outstanding_cr']", "SELECT total_credit_cr FROM v_total_industry_monthly", "=C_GrandTotal", "SPECIFIED"),
        ("KPI-02", "MoM Credit Change (â‚¹ Cr)", "C_t - C_t-1", "curr_credit - prev_month_credit", "curr.credit_outstanding_cr - prev_m.credit_outstanding_cr", "=C_t - C_prev_month", "SPECIFIED"),
        ("KPI-03", "MoM Credit Growth %", "((C_t - C_t-1) / C_t-1) * 100", "(mom_change / prev_month_credit) * 100", "ROUND(100.0 * mom_change / prev_month_credit, 2)", "=(C_t - C_prev_m)/C_prev_m * 100", "SPECIFIED"),
        ("KPI-04", "YoY Credit Change (â‚¹ Cr)", "C_t - C_t-12", "curr_credit - prev_year_credit", "curr.credit_outstanding_cr - prev_y.credit_outstanding_cr", "=C_t - C_prev_year", "SPECIFIED"),
        ("KPI-05", "YoY Credit Growth %", "((C_t - C_t-12) / C_t-12) * 100", "(yoy_change / prev_year_credit) * 100", "ROUND(100.0 * yoy_change / prev_year_credit, 2)", "=(C_t - C_prev_y)/C_prev_y * 100", "SPECIFIED"),
        ("KPI-06", "Sector Portfolio Share %", "(C_sector / C_total) * 100", "(credit_outstanding_cr / total_credit_cr) * 100", "ROUND(100.0 * curr / gt.total_credit_cr, 4)", "=C_sector / C_total * 100", "SPECIFIED"),
        ("KPI-07", "Top 3 Concentration Share %", "Sum of top 3 mutually exclusive sector shares", "top3['sector_share_pct'].sum()", "SUM(CASE WHEN rnk <= 3 THEN sector_share_pct END)", "=SUM(Top3_Shares)", "SPECIFIED"),
        ("KPI-08", "Herfindahl-Hirschman Index (HHI)", "Sum of squared fractional shares * 10,000", "sum((share_pct)^2)", "ROUND(SUM(POWER(sector_share_pct, 2)), 2)", "=SUMSQ(Shares_pct)", "SPECIFIED")
    ]

    for row_idx, row_data in enumerate(kpi_matrix_data, start=15):
        for col_idx, val in enumerate(row_data, start=2):
            cell = ws1.cell(row=row_idx, column=col_idx, value=val)
            cell.font = regular_font
            cell.border = thin_border
            if col_idx == 8:  # Status
                cell.fill = pass_fill
                cell.font = pass_font
                cell.alignment = Alignment(horizontal="center")

    # -------------------------------------------------------------
    # Tab 2: Cross-Tool Reconciliation Sample (Side-by-Side)
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="Cross-Tool Reconciliation")
    ws2.views.sheetView[0].showGridLines = True

    # Header
    ws2.merge_cells("A1:K2")
    ws2["A1"] = "KPI RECONCILIATION: PYTHON vs SQL vs EXCEL FORMULAS"
    ws2["A1"].font = white_title_font
    ws2["A1"].fill = navy_fill
    ws2["A1"].alignment = Alignment(horizontal="center", vertical="center")

    recon_headers = [
        "Reporting Month", "Sector Code", "Sector Name", "Credit Outstanding (â‚¹ Cr)",
        "Python YoY %", "SQL YoY %", "Excel YoY Formula",
        "Python Share %", "SQL Share %", "Excel Share Formula",
        "Reconciliation Audit", "Prior Year Credit", "Grand Total Credit"
    ]

    for col_idx, h in enumerate(recon_headers, start=1):
        cell = ws2.cell(row=3, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Load comparison rows from database
    db_path = os.path.join(data_dir, "processed", "credit_lens.db")
    conn = sqlite3.connect(db_path)
    # Sample periods: 2026-06 (latest), 2025-06, 2024-06, 2023-06, 2022-06, 2021-06, 2020-06
    query = """
    SELECT 
        reporting_month,
        sector_code,
        sector_name,
        credit_outstanding_cr,
        previous_year_credit_cr,
        grand_total_industry_credit_cr,
        yoy_growth_pct,
        sector_share_pct
    FROM v_sector_monthly_kpis
    WHERE is_mutually_exclusive = 1
      AND reporting_month IN ('2026-06', '2025-06', '2024-06', '2023-06')
    ORDER BY reporting_month DESC, credit_outstanding_cr DESC
    """
    df_sample = pd.read_sql_query(query, conn)
    conn.close()

    # Independent pandas calculations from cleaned source observations.
    df_python = pd.read_csv(os.path.join(data_dir, "processed", "credit_clean.csv"), dtype={"sector_code": str})
    df_python["period"] = pd.PeriodIndex(df_python["reporting_month"], freq="M")
    source_values = df_python.set_index(["sector_code", "period"])["credit_outstanding_cr"].to_dict()

    for idx, row in df_sample.iterrows():
        excel_row = idx + 4
        ws2.cell(row=excel_row, column=1, value=row["reporting_month"]).font = regular_font
        ws2.cell(row=excel_row, column=2, value=row["sector_code"]).font = regular_font
        ws2.cell(row=excel_row, column=3, value=row["sector_name"]).font = bold_font
        
        c_cell = ws2.cell(row=excel_row, column=4, value=float(row["credit_outstanding_cr"]))
        c_cell.font = regular_font
        c_cell.number_format = "#,##0.00"

        month_period = pd.Period(row["reporting_month"], freq="M")
        code = str(row["sector_code"])
        previous = source_values.get((code, month_period - 12))
        grand_total = source_values.get(("2", month_period))
        current = float(row["credit_outstanding_cr"])
        python_yoy = ((current - previous) / previous * 100.0) if previous else None
        python_share = (current / grand_total * 100.0) if grand_total else None
        ws2.cell(row=excel_row, column=12, value=previous)
        ws2.cell(row=excel_row, column=13, value=grand_total)

        # Python YoY independently derived from cleaned source records.
        py_yoy = ws2.cell(row=excel_row, column=5, value=python_yoy)
        py_yoy.font = regular_font
        py_yoy.number_format = "0.00"

        # SQL YoY
        sql_yoy = ws2.cell(row=excel_row, column=6, value=float(row["yoy_growth_pct"]) if pd.notna(row["yoy_growth_pct"]) else 0.0)
        sql_yoy.font = regular_font
        sql_yoy.number_format = "0.00"

        xl_yoy_cell = ws2.cell(row=excel_row, column=7, value=f'=IFERROR((D{excel_row}-L{excel_row})/L{excel_row}*100,"")')
        xl_yoy_cell.font = regular_font
        xl_yoy_cell.number_format = "0.00"

        # Python Share %
        py_sh = ws2.cell(row=excel_row, column=8, value=python_share)
        py_sh.font = regular_font
        py_sh.number_format = "0.0000"

        # SQL Share %
        sql_sh = ws2.cell(row=excel_row, column=9, value=round(float(row["sector_share_pct"]), 4))
        sql_sh.font = regular_font
        sql_sh.number_format = "0.0000"

        # Excel Share
        xl_sh_cell = ws2.cell(row=excel_row, column=10, value=f'=IFERROR(D{excel_row}/M{excel_row}*100,"")')
        xl_sh_cell.font = regular_font
        xl_sh_cell.number_format = "0.0000"

        # Audit status
        audit_cell = ws2.cell(row=excel_row, column=11, value=f'=IF(AND(ABS(E{excel_row}-F{excel_row})<0.01,ABS(E{excel_row}-G{excel_row})<0.01,ABS(H{excel_row}-I{excel_row})<0.01,ABS(H{excel_row}-J{excel_row})<0.01),"MATCH","MISMATCH")')
        audit_cell.font = pass_font
        audit_cell.fill = pass_fill
        audit_cell.alignment = Alignment(horizontal="center")

        for c in range(1, 14):
            ws2.cell(row=excel_row, column=c).border = thin_border

    # -------------------------------------------------------------
    # Tab 3: Monthly Concentration & HHI Series
    # -------------------------------------------------------------
    ws3 = wb.create_sheet(title="HHI & Concentration")
    ws3.views.sheetView[0].showGridLines = True

    ws3.merge_cells("A1:G2")
    ws3["A1"] = "PORTFOLIO CONCENTRATION: MONTHLY HHI & TOP-3 SECTOR SHARE"
    ws3["A1"].font = white_title_font
    ws3["A1"].fill = navy_fill
    ws3["A1"].alignment = Alignment(horizontal="center", vertical="center")

    hhi_headers = ["Reporting Month", "Total Mutually Exclusive Credit (â‚¹ Cr)", "HHI (Points 0-10,000)", "HHI (Fraction 0-1)", "Top 3 Share %", "Largest Sector", "Largest Sector Share %"]
    for col_idx, h in enumerate(hhi_headers, start=1):
        cell = ws3.cell(row=3, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center", vertical="center")

    conc_path = os.path.join(data_dir, "processed", "industry_concentration_monthly.csv")
    df_conc = pd.read_csv(conc_path)

    for idx, row in df_conc.iterrows():
        excel_row = idx + 4
        ws3.cell(row=excel_row, column=1, value=row["reporting_month"]).font = regular_font
        
        c2 = ws3.cell(row=excel_row, column=2, value=float(row["total_mutually_exclusive_credit_cr"]))
        c2.font = regular_font
        c2.number_format = "#,##0.00"

        c3 = ws3.cell(row=excel_row, column=3, value=float(row["hhi_index"]))
        c3.font = bold_font
        c3.number_format = "#,##0.00"

        c4 = ws3.cell(row=excel_row, column=4, value=float(row["hhi_fraction"]))
        c4.font = regular_font
        c4.number_format = "0.0000"

        c5 = ws3.cell(row=excel_row, column=5, value=float(row["top3_concentration_share_pct"]))
        c5.font = bold_font
        c5.number_format = "0.00"

        ws3.cell(row=excel_row, column=6, value=row["largest_sector"]).font = regular_font
        
        c7 = ws3.cell(row=excel_row, column=7, value=float(row["largest_sector_share_pct"]))
        c7.font = regular_font
        c7.number_format = "0.00"

        for c in range(1, 8):
            ws3.cell(row=excel_row, column=c).border = thin_border

    # Adjust column widths automatically
    for sheet in [ws1, ws2, ws3]:
        for col in sheet.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    wb.save(output_path)
    return output_path


if __name__ == "__main__":
    path = generate_excel_reconciliation()
    print("Reconciliation workbook generated successfully at:", path)


