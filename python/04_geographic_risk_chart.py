"""
US Financial Loan Monitoring System
Script: 04_geographic_risk_chart.py
Output: outputs/geographic_risk.png

Dashboard Page 3 — Geographic Risk Concentration
  - US state choropleth heat map (delinquency rate by state)
  - Top 15 states bar chart (delinquency rate + portfolio balance)
  - Risk tier flags: CRITICAL / HIGH / ELEVATED / NORMAL
  - State risk vs national average multiplier table
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────
BASE     = "/home/claude/us-financial-loan-monitoring"
DATA_IN  = f"{BASE}/data/processed/loan_portfolio_scored.csv"
OUT_FILE = f"{BASE}/outputs/geographic_risk.png"

# ── Colours ────────────────────────────────────────────────────
DARK_BG  = "#0d1b2a"
MID_BG   = "#1a3c5e"
C_BLUE   = "#2d7dd2"
C_RED    = "#e8523a"
C_AMBER  = "#f39c12"
C_GREEN  = "#27ae60"
C_WHITE  = "#ecf0f1"
C_GREY   = "#95a5a6"

# Risk tier colours
TIER_COLORS = {
    "CRITICAL":  "#c0392b",
    "HIGH":      "#e67e22",
    "ELEVATED":  "#f39c12",
    "NORMAL":    "#2d7dd2",
}

# ── State coordinates (centre points for scatter map) ─────────
# lat/lon approximate centres of each US state
STATE_COORDS = {
    "AL":(32.8,-86.8),"AK":(64.2,-153.4),"AZ":(34.3,-111.1),"AR":(34.8,-92.2),
    "CA":(37.2,-119.5),"CO":(39.0,-105.5),"CT":(41.6,-72.7),"DE":(39.0,-75.5),
    "FL":(28.6,-82.4),"GA":(32.7,-83.4),"HI":(20.3,-156.3),"ID":(44.4,-114.6),
    "IL":(40.0,-89.2),"IN":(39.9,-86.3),"IA":(42.1,-93.5),"KS":(38.5,-98.4),
    "KY":(37.5,-85.3),"LA":(30.9,-91.8),"ME":(45.4,-69.2),"MD":(39.0,-76.8),
    "MA":(42.3,-71.8),"MI":(44.3,-85.4),"MN":(46.4,-93.2),"MS":(32.7,-89.7),
    "MO":(38.4,-92.5),"MT":(47.0,-110.0),"NE":(41.5,-99.9),"NV":(39.3,-116.6),
    "NH":(43.7,-71.6),"NJ":(40.1,-74.5),"NM":(34.4,-106.1),"NY":(42.9,-75.6),
    "NC":(35.5,-79.4),"ND":(47.5,-100.5),"OH":(40.4,-82.8),"OK":(35.6,-97.5),
    "OR":(44.0,-120.5),"PA":(40.9,-77.8),"RI":(41.7,-71.5),"SC":(33.9,-80.9),
    "SD":(44.4,-100.2),"TN":(35.9,-86.4),"TX":(31.5,-99.3),"UT":(39.3,-111.1),
    "VT":(44.1,-72.7),"VA":(37.5,-79.4),"WA":(47.4,-120.6),"WV":(38.6,-80.6),
    "WI":(44.3,-89.8),"WY":(43.0,-107.6)
}

# ── Load data ──────────────────────────────────────────────────
print("Loading data...")
df = pd.read_csv(DATA_IN, parse_dates=["origination_date"])
df["is_delinquent"] = (df["delinquency_status"] != "Current").astype(int)
df["is_default"]    = df["delinquency_status"].isin(["Default","Charged-Off"]).astype(int)
print(f"  {len(df):,} loans loaded across {df['state'].nunique()} states")

# ── State-level aggregation ────────────────────────────────────
state_stats = df.groupby("state").agg(
    loan_count      = ("loan_id",         "count"),
    total_balance   = ("loan_amount",     "sum"),
    avg_credit_score= ("credit_score",    "mean"),
    avg_dti         = ("dti_ratio",       "mean"),
    avg_pd          = ("model_pd",        "mean"),
    delinquent_count= ("is_delinquent",   "sum"),
    default_count   = ("is_default",      "sum"),
).reset_index()

state_stats["delinquency_rate"] = state_stats["delinquent_count"] / state_stats["loan_count"]
state_stats["default_rate"]     = state_stats["default_count"]    / state_stats["loan_count"]
state_stats["balance_M"]        = state_stats["total_balance"] / 1e6

# National average
nat_avg = state_stats["delinquency_rate"].mean()

# Risk tier assignment
def risk_tier(rate, nat_avg):
    if   rate > nat_avg * 2.0: return "CRITICAL"
    elif rate > nat_avg * 1.5: return "HIGH"
    elif rate > nat_avg * 1.0: return "ELEVATED"
    else:                      return "NORMAL"

state_stats["risk_multiplier"] = (state_stats["delinquency_rate"] / nat_avg).round(2)
state_stats["risk_tier"]       = state_stats["delinquency_rate"].apply(lambda r: risk_tier(r, nat_avg))

# Add coordinates
state_stats["lat"] = state_stats["state"].map(lambda s: STATE_COORDS.get(s, (None,None))[0])
state_stats["lon"] = state_stats["state"].map(lambda s: STATE_COORDS.get(s, (None,None))[1])
state_stats = state_stats.dropna(subset=["lat","lon"])

print(f"  National avg delinquency rate: {nat_avg:.1%}")
print(f"  Risk tiers: {state_stats['risk_tier'].value_counts().to_dict()}")

# ── Figure ─────────────────────────────────────────────────────
fig = plt.figure(figsize=(20, 16))
fig.patch.set_facecolor(DARK_BG)
gs = gridspec.GridSpec(3, 2, figure=fig,
                       hspace=0.45, wspace=0.3,
                       height_ratios=[2.2, 1.4, 1.4])

def style_ax(ax):
    ax.set_facecolor(DARK_BG)
    for spine in ax.spines.values(): spine.set_color("#2a4a6b")
    ax.tick_params(colors=C_WHITE, labelsize=9)
    ax.xaxis.label.set_color(C_GREY)
    ax.yaxis.label.set_color(C_GREY)


# ── Panel 1: US Scatter Map (spans full top row) ───────────────
ax_map = fig.add_subplot(gs[0, :])
style_ax(ax_map)

# Custom colormap: blue (low) → amber → red (high)
cmap = LinearSegmentedColormap.from_list(
    "risk", ["#2d7dd2", "#f39c12", "#e8523a"], N=256
)

sc = ax_map.scatter(
    state_stats["lon"], state_stats["lat"],
    c=state_stats["delinquency_rate"],
    cmap=cmap, s=state_stats["loan_count"] * 2.5,
    alpha=0.85, edgecolors="#0d1b2a", linewidths=0.8,
    zorder=3
)

# State labels
for _, row in state_stats.iterrows():
    ax_map.annotate(
        row["state"],
        (row["lon"], row["lat"]),
        ha="center", va="center",
        fontsize=6.5, color=C_WHITE, fontweight="bold",
        zorder=4
    )

# Colour bar
cbar = plt.colorbar(sc, ax=ax_map, orientation="vertical",
                    fraction=0.02, pad=0.01)
cbar.ax.yaxis.set_tick_params(color=C_WHITE, labelsize=8)
cbar.set_label("Delinquency Rate", color=C_GREY, fontsize=9)
plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color=C_WHITE)
cbar.ax.set_facecolor(DARK_BG)

# Risk tier legend (bubble size)
for tier, colour in TIER_COLORS.items():
    ax_map.scatter([], [], c=colour, s=80, label=tier, alpha=0.85)
ax_map.legend(loc="lower left", facecolor=MID_BG, labelcolor=C_WHITE,
              fontsize=8, framealpha=0.9, title="Risk Tier",
              title_fontsize=8)

ax_map.set_xlim(-130, -65)
ax_map.set_ylim(24, 50)
ax_map.set_title("Geographic Risk Concentration — Delinquency Rate by State\n"
                 "(bubble size = loan count)",
                 color=C_WHITE, fontsize=13, pad=12)
ax_map.set_xlabel("Longitude")
ax_map.set_ylabel("Latitude")

# National average annotation
ax_map.annotate(
    f"National avg: {nat_avg:.1%}",
    xy=(0.02, 0.06), xycoords="axes fraction",
    color=C_AMBER, fontsize=9, fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.3", facecolor=MID_BG, alpha=0.8)
)


# ── Panel 2: Top 15 States — Delinquency Rate ─────────────────
ax2 = fig.add_subplot(gs[1, 0])
style_ax(ax2)

top15_delq = state_stats.nlargest(15, "delinquency_rate").sort_values("delinquency_rate")
bar_colors = [TIER_COLORS[t] for t in top15_delq["risk_tier"]]
bars = ax2.barh(top15_delq["state"], top15_delq["delinquency_rate"] * 100,
                color=bar_colors, edgecolor="none", height=0.7)
ax2.axvline(nat_avg * 100, color=C_AMBER, linestyle="--",
            linewidth=1.5, alpha=0.9, label=f"National avg {nat_avg:.1%}")
for bar, val in zip(bars, top15_delq["delinquency_rate"]):
    ax2.text(val * 100 + 0.3, bar.get_y() + bar.get_height() / 2,
             f"{val:.1%}", va="center", fontsize=8, color=C_WHITE)
ax2.set_title("Top 15 States — Delinquency Rate (%)",
              color=C_WHITE, fontsize=11, pad=8)
ax2.set_xlabel("Delinquency Rate (%)")
ax2.legend(facecolor=MID_BG, labelcolor=C_WHITE, fontsize=8)


# ── Panel 3: Top 15 States — Portfolio Balance ────────────────
ax3 = fig.add_subplot(gs[1, 1])
style_ax(ax3)

top15_bal = state_stats.nlargest(15, "total_balance").sort_values("total_balance")
ax3.barh(top15_bal["state"], top15_bal["balance_M"],
         color=C_BLUE, edgecolor="none", height=0.7)
for i, (_, row) in enumerate(top15_bal.iterrows()):
    ax3.text(row["balance_M"] + 0.3, i,
             f"${row['balance_M']:.0f}M", va="center", fontsize=8, color=C_WHITE)
ax3.set_title("Top 15 States — Portfolio Balance ($M)",
              color=C_WHITE, fontsize=11, pad=8)
ax3.set_xlabel("Portfolio Balance ($M)")


# ── Panel 4: Risk Tier Distribution ───────────────────────────
ax4 = fig.add_subplot(gs[2, 0])
style_ax(ax4)

tier_order  = ["CRITICAL","HIGH","ELEVATED","NORMAL"]
tier_counts = state_stats["risk_tier"].value_counts().reindex(tier_order, fill_value=0)
tier_cols   = [TIER_COLORS[t] for t in tier_order]
wedges, texts, autotexts = ax4.pie(
    tier_counts.values,
    labels=tier_order,
    colors=tier_cols,
    autopct="%1.0f%%",
    startangle=90,
    pctdistance=0.75,
    wedgeprops=dict(width=0.55, edgecolor=DARK_BG, linewidth=2),
)
for t in texts:      t.set_color(C_WHITE); t.set_fontsize(9)
for t in autotexts:  t.set_color(DARK_BG);  t.set_fontsize(9); t.set_fontweight("bold")
ax4.set_title("States by Risk Tier",
              color=C_WHITE, fontsize=11, pad=8)


# ── Panel 5: Risk Multiplier — Top 10 States ──────────────────
ax5 = fig.add_subplot(gs[2, 1])
style_ax(ax5)

top10_mult = state_stats.nlargest(10, "risk_multiplier").sort_values("risk_multiplier")
mult_colors = [TIER_COLORS[t] for t in top10_mult["risk_tier"]]
bars5 = ax5.barh(top10_mult["state"], top10_mult["risk_multiplier"],
                 color=mult_colors, edgecolor="none", height=0.7)
ax5.axvline(1.0, color=C_WHITE, linestyle="--", linewidth=1, alpha=0.4,
            label="National average (1.0×)")
ax5.axvline(1.5, color=C_AMBER, linestyle=":", linewidth=1, alpha=0.6,
            label="HIGH threshold (1.5×)")
ax5.axvline(2.0, color=C_RED,   linestyle=":", linewidth=1, alpha=0.6,
            label="CRITICAL threshold (2.0×)")
for bar, val in zip(bars5, top10_mult["risk_multiplier"]):
    ax5.text(val + 0.02, bar.get_y() + bar.get_height() / 2,
             f"{val:.2f}×", va="center", fontsize=8, color=C_WHITE)
ax5.set_title("Top 10 States — Risk Multiplier vs National Avg",
              color=C_WHITE, fontsize=11, pad=8)
ax5.set_xlabel("Risk Multiplier (state rate ÷ national rate)")
ax5.legend(facecolor=MID_BG, labelcolor=C_WHITE, fontsize=7, loc="lower right")

# ── Supertitle ─────────────────────────────────────────────────
fig.suptitle(
    "Dashboard Page 3  —  Geographic Risk Concentration",
    color=C_WHITE, fontsize=16, fontweight="bold", y=0.99
)

plt.savefig(OUT_FILE, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close()
print(f"Saved: {OUT_FILE}")
