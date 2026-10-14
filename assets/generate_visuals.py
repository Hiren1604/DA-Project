"""
CreditLens Visual Generator Module.
Generates institutional research charts and dashboard preview screenshots
following the palette and UX guidelines in the CreditLens Blueprint.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import pandas as pd
import numpy as np

# Styling configuration
BG_COLOR = "#0D1525"
CARD_BG = "#152238"
ACCENT_CYAN = "#06B6D4"
ACCENT_TEAL = "#14B8A6"
ACCENT_AMBER = "#F59E0B"
TEXT_COLOR = "#F8FAFC"
MUTED_TEXT = "#94A3B8"
GRID_COLOR = "#1E293B"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
    "text.color": TEXT_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "xtick.color": MUTED_TEXT,
    "ytick.color": MUTED_TEXT,
    "figure.facecolor": BG_COLOR,
    "axes.facecolor": CARD_BG,
    "axes.edgecolor": GRID_COLOR,
    "grid.color": GRID_COLOR,
    "grid.alpha": 0.5,
})


def format_cr(val, pos=None):
    if val >= 100000:
        return f"₹{val/100000:.1f}L Cr"
    return f"₹{val/1000:.0f}k Cr"


def generate_all_visuals(data_dir: str = "data", output_dir: str = "assets/dashboard_screenshots"):
    os.makedirs(output_dir, exist_ok=True)
    proc_dir = os.path.join(data_dir, "processed")

    df_metrics = pd.read_csv(os.path.join(proc_dir, "sector_monthly_metrics.csv"))
    df_metrics["reporting_date"] = pd.to_datetime(df_metrics["reporting_date"])
    df_conc = pd.read_csv(os.path.join(proc_dir, "industry_concentration_monthly.csv"))

    # -------------------------------------------------------------
    # Visual 1: Page 1 — Executive Credit Overview
    # -------------------------------------------------------------
    fig = plt.figure(figsize=(16, 9), dpi=200)
    gs = fig.add_gridspec(3, 2, height_ratios=[0.8, 2.2, 2.2], hspace=0.35, wspace=0.25)

    # Top KPI Banner
    ax_banner = fig.add_subplot(gs[0, :])
    ax_banner.axis("off")
    ax_banner.set_facecolor(BG_COLOR)

    # Header text
    ax_banner.text(0.0, 0.85, "CreditLens — Indian Banking & Credit Portfolio Analytics", fontsize=16, fontweight="bold", color=TEXT_COLOR)
    ax_banner.text(0.0, 0.60, "Official RBI DBIE Table 16 • As of June 30, 2026 • Reporting Unit: ₹ Crore", fontsize=10, color=ACCENT_CYAN)

    # KPI Cards in Banner
    cards = [
        ("TOTAL INDUSTRY CREDIT", "₹47,71,513 Cr", "+19.24% YoY", ACCENT_TEAL, 0.0),
        ("MONTH-OVER-MONTH GROWTH", "+3.19%", "+₹1,47,609 Cr MoM", ACCENT_CYAN, 0.26),
        ("TOP 3 SECTOR CONCENTRATION", "50.72%", "Infrastructure, Metals, Other", ACCENT_AMBER, 0.52),
        ("HERFINDAHL INDEX (HHI)", "1,431.3 pts", "Moderate Concentration", "#A855F7", 0.78),
    ]

    for label, val, sub, col, x_pos in cards:
        rect = plt.Rectangle((x_pos, 0.0), 0.23, 0.45, transform=ax_banner.transAxes,
                             facecolor=CARD_BG, edgecolor=GRID_COLOR, linewidth=1, zorder=2)
        ax_banner.add_patch(rect)
        ax_banner.text(x_pos + 0.02, 0.32, label, transform=ax_banner.transAxes, fontsize=8, color=MUTED_TEXT, fontweight="bold")
        ax_banner.text(x_pos + 0.02, 0.16, val, transform=ax_banner.transAxes, fontsize=13, color=col, fontweight="bold")
        ax_banner.text(x_pos + 0.02, 0.04, sub, transform=ax_banner.transAxes, fontsize=8, color=TEXT_COLOR)

    # Chart 1A: Historical Total Credit Trend
    ax_trend = fig.add_subplot(gs[1, 0])
    df_tot = df_metrics[df_metrics["sector_code"] == "2"].sort_values("reporting_date")
    ax_trend.plot(df_tot["reporting_date"], df_tot["credit_outstanding_cr"], color=ACCENT_CYAN, linewidth=2.5, label="Total Industry Credit")
    ax_trend.fill_between(df_tot["reporting_date"], df_tot["credit_outstanding_cr"], color=ACCENT_CYAN, alpha=0.15)
    ax_trend.yaxis.set_major_formatter(ticker.FuncFormatter(format_cr))
    ax_trend.set_title("Total Industry Credit Trajectory (2019 – 2026)", fontsize=11, fontweight="bold", pad=12)
    ax_trend.grid(True, linestyle="--", alpha=0.4)
    # Add vertical line for July 2023 merger
    ax_trend.axvline(pd.Timestamp("2023-07-28"), color=ACCENT_AMBER, linestyle=":", alpha=0.8, label="July 2023 Bank-NBFC Merger")
    ax_trend.legend(loc="upper left", frameon=False, fontsize=8)

    # Chart 1B: Ranked Top Sectors Exposure (Latest Month)
    ax_ranked = fig.add_subplot(gs[1, 1])
    latest_date = df_metrics["reporting_date"].max()
    df_l1_latest = df_metrics[(df_metrics["reporting_date"] == latest_date) & (df_metrics["is_mutually_exclusive"] == True)].sort_values("credit_outstanding_cr", ascending=True).tail(8)
    
    colors = [ACCENT_TEAL if i >= len(df_l1_latest)-3 else "#3B82F6" for i in range(len(df_l1_latest))]
    bars = ax_ranked.barh(df_l1_latest["sector_name"], df_l1_latest["credit_outstanding_cr"], color=colors, height=0.65)
    ax_ranked.xaxis.set_major_formatter(ticker.FuncFormatter(format_cr))
    ax_ranked.set_title("Top 8 Industry Exposures (June 2026)", fontsize=11, fontweight="bold", pad=12)
    ax_ranked.grid(True, axis="x", linestyle="--", alpha=0.4)
    for bar in bars:
        w = bar.get_width()
        ax_ranked.text(w + 15000, bar.get_y() + bar.get_height()/2, format_cr(w), va="center", ha="left", fontsize=8, color=TEXT_COLOR)

    # Chart 1C: Year-over-Year Growth Comparison (Top 8)
    ax_yoy = fig.add_subplot(gs[2, 0])
    df_yoy = df_metrics[(df_metrics["reporting_date"] == latest_date) & (df_metrics["is_mutually_exclusive"] == True)].sort_values("credit_outstanding_cr", ascending=False).head(8)
    yoy_bars = ax_yoy.bar(df_yoy["sector_name"], df_yoy["yoy_growth_pct"], color=ACCENT_TEAL, width=0.55)
    ax_yoy.set_title("YoY Credit Growth % for Leading Sectors (June 2026)", fontsize=11, fontweight="bold", pad=12)
    ax_yoy.set_ylabel("Growth (%)", fontsize=9)
    ax_yoy.set_xticklabels(df_yoy["sector_name"], rotation=30, ha="right", fontsize=8)
    ax_yoy.grid(True, axis="y", linestyle="--", alpha=0.4)
    for bar in yoy_bars:
        h = bar.get_height()
        ax_yoy.text(bar.get_x() + bar.get_width()/2, h + 0.8, f"{h:.1f}%", ha="center", va="bottom", fontsize=8, color=TEXT_COLOR)

    # Chart 1D: Concentration Breakdown (Top 3 vs Rest)
    ax_pie = fig.add_subplot(gs[2, 1])
    top3_val = df_l1_latest.tail(3)["credit_outstanding_cr"].sum()
    rest_val = df_metrics[(df_metrics["reporting_date"] == latest_date) & (df_metrics["is_mutually_exclusive"] == True)]["credit_outstanding_cr"].sum() - top3_val
    wedges, texts, autotexts = ax_pie.pie(
        [top3_val, rest_val],
        labels=["Top 3 Sectors\n(50.7%)", "Remaining 16 Sectors\n(49.3%)"],
        colors=[ACCENT_AMBER, "#334155"],
        autopct="%1.1f%%",
        startangle=140,
        pctdistance=0.6,
        wedgeprops=dict(width=0.45, edgecolor=BG_COLOR)
    )
    for at in autotexts:
        at.set_color(TEXT_COLOR)
        at.set_fontweight("bold")
    ax_pie.set_title("Industrial Credit Allocation (June 2026)", fontsize=11, fontweight="bold", pad=12)

    p1_path = os.path.join(output_dir, "executive_credit_overview.png")
    plt.savefig(p1_path, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close()

    # -------------------------------------------------------------
    # Visual 2: Page 2 — Sector Exposure & Concentration Analysis
    # -------------------------------------------------------------
    fig2, (ax2_1, ax2_2) = plt.subplots(1, 2, figsize=(16, 7), dpi=200, gridspec_kw={"wspace": 0.25})

    # HHI Time Series
    df_conc_sorted = df_conc.sort_values("reporting_month")
    conc_dates = pd.to_datetime(df_conc_sorted["reporting_month"] + "-01")
    ax2_1.plot(conc_dates, df_conc_sorted["hhi_index"], color=ACCENT_CYAN, linewidth=2.5, label="HHI Index (Points)")
    ax2_1.axhline(1500, color=ACCENT_AMBER, linestyle="--", linewidth=1.5, label="Moderate Concentration Threshold (1,500)")
    ax2_1.axhline(1000, color=ACCENT_TEAL, linestyle="--", linewidth=1.5, label="Unconcentrated Threshold (1,000)")
    ax2_1.set_title("Herfindahl-Hirschman Index (HHI) Trajectory (2019 – 2026)", fontsize=11, fontweight="bold", pad=12)
    ax2_1.set_ylabel("HHI (Points 0 – 10,000)", fontsize=9)
    ax2_1.grid(True, linestyle="--", alpha=0.4)
    ax2_1.legend(loc="lower right", frameon=False, fontsize=8)

    # Top-3 Share Trajectory
    ax2_2.plot(conc_dates, df_conc_sorted["top3_concentration_share_pct"], color=ACCENT_AMBER, linewidth=2.5, label="Top 3 Sectors Exposure Share %")
    ax2_2.fill_between(conc_dates, df_conc_sorted["top3_concentration_share_pct"], color=ACCENT_AMBER, alpha=0.15)
    ax2_2.set_title("Top 3 Sectors Concentration Share % (2019 – 2026)", fontsize=11, fontweight="bold", pad=12)
    ax2_2.set_ylabel("Share of Industrial Credit (%)", fontsize=9)
    ax2_2.grid(True, linestyle="--", alpha=0.4)
    ax2_2.legend(loc="lower right", frameon=False, fontsize=8)

    p2_path = os.path.join(output_dir, "sector_exposure_concentration.png")
    plt.savefig(p2_path, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close()

    # -------------------------------------------------------------
    # Visual 3: Page 3 — Indexed Growth & Historical Trends
    # -------------------------------------------------------------
    fig3, ax3 = plt.subplots(figsize=(14, 7), dpi=200)

    # Focus on top 6 sectors
    top6_codes = ["2.18", "2.13", "2.19", "2.14", "2.9", "2.2"]
    colors_dict = {
        "2.18": "#06B6D4",  # Infra
        "2.13": "#F59E0B",  # Metals
        "2.19": "#10B981",  # Other
        "2.14": "#8B5CF6",  # Engineering
        "2.9":  "#EC4899",  # Chemicals
        "2.2":  "#3B82F6",  # Food
    }

    for code in top6_codes:
        sec_df = df_metrics[df_metrics["sector_code"] == code].sort_values("reporting_date")
        label_name = sec_df.iloc[0]["sector_name"]
        ax3.plot(sec_df["reporting_date"], sec_df["credit_indexed_base100"], label=label_name, color=colors_dict[code], linewidth=2.0)

    ax3.axhline(100, color=MUTED_TEXT, linestyle=":", alpha=0.7, label="Baseline (Jan 2019 = 100)")
    ax3.axvline(pd.Timestamp("2023-07-28"), color="#EF4444", linestyle="--", alpha=0.7, label="Structural Break: Merger (July 2023)")
    ax3.set_title("Indexed Sector Growth Trajectory (January 2019 = 100)", fontsize=12, fontweight="bold", pad=14)
    ax3.set_ylabel("Index (Base = 100)", fontsize=10)
    ax3.grid(True, linestyle="--", alpha=0.4)
    ax3.legend(loc="upper left", frameon=True, facecolor=CARD_BG, edgecolor=GRID_COLOR, fontsize=8)

    p3_path = os.path.join(output_dir, "sector_indexed_growth.png")
    plt.savefig(p3_path, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close()

    # -------------------------------------------------------------
    # Visual 4: Monthly YoY Growth Heatmap
    # -------------------------------------------------------------
    fig4, ax4 = plt.subplots(figsize=(12, 6), dpi=200)
    df_tot_m = df_metrics[df_metrics["sector_code"] == "2"].copy()
    df_tot_m["month"] = df_tot_m["reporting_date"].dt.month
    df_tot_m["year"] = df_tot_m["reporting_date"].dt.year
    pivot_yoy = df_tot_m.pivot(index="year", columns="month", values="yoy_growth_pct")
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    pivot_yoy.columns = [month_names[m-1] for m in pivot_yoy.columns]

    sns.heatmap(pivot_yoy, annot=True, fmt=".1f", cmap="YlGnBu", cbar_kws={"label": "YoY Growth %"}, ax=ax4, linewidths=0.5, linecolor=BG_COLOR)
    ax4.set_title("Total Industrial Bank Credit — YoY Growth Heatmap (%)", fontsize=11, fontweight="bold", pad=12)
    ax4.set_ylabel("Year", fontsize=9)
    ax4.set_xlabel("Month", fontsize=9)

    p4_path = os.path.join(output_dir, "growth_heatmap.png")
    plt.savefig(p4_path, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close()

    return [p1_path, p2_path, p3_path, p4_path]


if __name__ == "__main__":
    generated = generate_all_visuals()
    print("Visualizations generated successfully:")
    for g in generated:
        print(" -", g)
