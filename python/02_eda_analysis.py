"""
US Financial Loan Monitoring System
File: 02_eda_analysis.py
Description: Standalone Exploratory Data Analysis script.
             Produces a second dashboard-style summary chart
             focused on portfolio composition and geographic risk.

Output: outputs/portfolio_overview.png
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings("ignore")

BASE     = "/home/claude/us-financial-loan-monitoring"
DATA_IN  = f"{BASE}/data/processed/loan_portfolio_scored.csv"
OUT_FILE = f"{BASE}/outputs/portfolio_overview.png"

DARK_BG  = "#0d1b2a"
MID_BG   = "#1a3c5e"
C_BLUE   = "#2d7dd2"
C_RED    = "#e8523a"
C_GREEN  = "#27ae60"
C_GOLD   = "#f39c12"
C_GREY   = "#95a5a6"
C_WHITE  = "#ecf0f1"

TIER_COLORS = {
    "Prime":        "#2d7dd2",
    "Near-Prime":   "#f39c12",
    "Subprime":     "#e67e22",
    "Deep Subprime":"#e8523a",
}

# ── Load ───────────────────────────────────────────────────────
df = pd.read_csv(DATA_IN, parse_dates=["origination_date"])
df["is_delinquent"] = (df["delinquency_status"] != "Current").astype(int)
df["is_default"]    = df["delinquency_status"].isin(["Default", "Charged-Off"]).astype(int)
print(f"Loaded {len(df):,} records")

# ── Canvas ─────────────────────────────────────────────────────
fig = plt.figure(figsize=(20, 15))
fig.patch.set_facecolor(DARK_BG)
gs  = gridspec.GridSpec(3, 3, figure=fig, hspace=0.5, wspace=0.38)

def style_ax(ax):
    ax.set_facecolor(DARK_BG)
    for spine in ax.spines.values():
        spine.set_color("#2a4a6b")
    ax.tick_params(colors=C_WHITE, labelsize=9)
    ax.xaxis.label.set_color(C_GREY)
    ax.yaxis.label.set_color(C_GREY)


# ── Panel 1: Portfolio Balance by Loan Type ────────────────────
ax1 = fig.add_subplot(gs[0, 0])
style_ax(ax1)
bal_by_type = df.groupby("loan_type")["loan_amount"].sum().sort_values()
colors_p1   = [C_BLUE if v >= bal_by_type.mean() else C_GREY for v in bal_by_type.values]
bars = ax1.barh(bal_by_type.index, bal_by_type.values / 1e6, color=colors_p1, edgecolor="none")
for bar, val in zip(bars, bal_by_type.values):
    ax1.text(val/1e6 + 0.5, bar.get_y() + bar.get_height()/2,
             f"${val/1e6:.0f}M", va="center", fontsize=8, color=C_WHITE)
ax1.set_title("Portfolio Balance by Loan Type ($M)", color=C_WHITE, fontsize=11, pad=10)
ax1.set_xlabel("Total Balance ($M)")


# ── Panel 2: Loan Count Share (Donut proxy) ───────────────────
ax2 = fig.add_subplot(gs[0, 1])
style_ax(ax2)
counts = df["loan_type"].value_counts()
pie_colors = [C_BLUE, C_GOLD, C_GREEN, C_RED, "#9b59b6", C_GREY]
wedges, texts, autotexts = ax2.pie(
    counts.values, labels=counts.index,
    autopct="%1.1f%%", colors=pie_colors,
    startangle=90, pctdistance=0.82,
    wedgeprops=dict(width=0.55, edgecolor=DARK_BG, linewidth=2)
)
for t in texts:      t.set_color(C_WHITE); t.set_fontsize(8)
for t in autotexts:  t.set_color(DARK_BG);  t.set_fontsize(8); t.set_fontweight("bold")
ax2.set_title("Portfolio Composition\n(Loan Count %)", color=C_WHITE, fontsize=11, pad=6)


# ── Panel 3: Origination Trend by Year ────────────────────────
ax3 = fig.add_subplot(gs[0, 2])
style_ax(ax3)
orig_yr = df.groupby(["origination_year","loan_type"])["loan_amount"].sum().unstack(fill_value=0)
orig_yr_m = orig_yr / 1e6
bottom = np.zeros(len(orig_yr_m))
stk_colors = [C_BLUE, C_GOLD, C_GREEN, C_RED, "#9b59b6", C_GREY]
for col, color in zip(orig_yr_m.columns, stk_colors):
    ax3.bar(orig_yr_m.index.astype(str), orig_yr_m[col], bottom=bottom,
            label=col, color=color, edgecolor="none")
    bottom += orig_yr_m[col].values
ax3.set_title("Origination Volume by Year ($M)", color=C_WHITE, fontsize=11, pad=10)
ax3.set_xlabel("Year")
ax3.set_ylabel("Volume ($M)")
ax3.legend(loc="upper left", facecolor=MID_BG, labelcolor=C_WHITE, fontsize=7, framealpha=0.8)


# ── Panel 4: Borrower Segment Distribution ────────────────────
ax4 = fig.add_subplot(gs[1, 0])
style_ax(ax4)
seg_order  = ["Prime","Near-Prime","Subprime","Deep Subprime"]
seg_counts = df["borrower_segment"].value_counts().reindex(seg_order, fill_value=0)
bar_colors = [TIER_COLORS.get(s, C_GREY) for s in seg_order]
bars4 = ax4.bar(seg_order, seg_counts.values, color=bar_colors, edgecolor="none")
for bar, val in zip(bars4, seg_counts.values):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
             f"{val:,}", ha="center", va="bottom", color=C_WHITE, fontsize=9)
ax4.set_title("Borrower Segment Distribution", color=C_WHITE, fontsize=11, pad=10)
ax4.set_ylabel("Loan Count")
plt.setp(ax4.get_xticklabels(), rotation=15, ha="right")


# ── Panel 5: Interest Rate Distribution by Segment ───────────
ax5 = fig.add_subplot(gs[1, 1])
style_ax(ax5)
for seg, color in TIER_COLORS.items():
    subset = df[df["borrower_segment"] == seg]["interest_rate"] * 100
    if len(subset) > 0:
        ax5.hist(subset, bins=25, alpha=0.6, color=color, label=seg, edgecolor="none")
ax5.set_title("Interest Rate Distribution by Segment", color=C_WHITE, fontsize=11, pad=10)
ax5.set_xlabel("Interest Rate (%)")
ax5.set_ylabel("Frequency")
ax5.legend(facecolor=MID_BG, labelcolor=C_WHITE, fontsize=8, framealpha=0.8)


# ── Panel 6: Delinquency Rate by Origination Year ─────────────
ax6 = fig.add_subplot(gs[1, 2])
style_ax(ax6)
delq_yr = (
    df.groupby("origination_year")["is_delinquent"]
    .agg(["mean","count"])
    .rename(columns={"mean":"rate","count":"n"})
)
delq_yr["rate_pct"] = delq_yr["rate"] * 100
ax6.bar(delq_yr.index.astype(str), delq_yr["rate_pct"],
        color=[C_RED if v > delq_yr["rate_pct"].mean() else C_BLUE
               for v in delq_yr["rate_pct"]], edgecolor="none")
ax6.axhline(delq_yr["rate_pct"].mean(), color=C_GOLD, linestyle="--",
            linewidth=1.5, alpha=0.9, label=f"Avg {delq_yr['rate_pct'].mean():.1f}%")
ax6.set_title("Delinquency Rate by Origination Year", color=C_WHITE, fontsize=11, pad=10)
ax6.set_ylabel("Delinquency Rate (%)")
ax6.set_xlabel("Origination Year")
ax6.legend(facecolor=MID_BG, labelcolor=C_WHITE, fontsize=9)


# ── Panel 7: Top 15 States — Loan Balance ─────────────────────
ax7 = fig.add_subplot(gs[2, 0])
style_ax(ax7)
state_bal = df.groupby("state")["loan_amount"].sum().sort_values(ascending=False).head(15)
bars7 = ax7.bar(state_bal.index, state_bal.values / 1e6,
                color=C_BLUE, edgecolor="none")
ax7.set_title("Top 15 States by Portfolio Balance ($M)", color=C_WHITE, fontsize=11, pad=10)
ax7.set_ylabel("Balance ($M)")
ax7.set_xlabel("State")


# ── Panel 8: State Delinquency Rate — Top 15 at Risk ──────────
ax8 = fig.add_subplot(gs[2, 1])
style_ax(ax8)
state_delq = (
    df.groupby("state")["is_delinquent"].mean()
    .sort_values(ascending=False)
    .head(15) * 100
)
ax8.bar(state_delq.index, state_delq.values,
        color=[C_RED if v > state_delq.mean() else C_GOLD for v in state_delq.values],
        edgecolor="none")
ax8.axhline(state_delq.mean(), color=C_WHITE, linestyle="--",
            linewidth=1, alpha=0.5, label=f"Avg {state_delq.mean():.1f}%")
ax8.set_title("Top 15 High-Risk States (Delinquency %)", color=C_WHITE, fontsize=11, pad=10)
ax8.set_ylabel("Delinquency Rate (%)")
ax8.set_xlabel("State")
ax8.legend(facecolor=MID_BG, labelcolor=C_WHITE, fontsize=9)


# ── Panel 9: PD Score vs Delinquency Scatter (Sample) ─────────
ax9 = fig.add_subplot(gs[2, 2])
style_ax(ax9)
sample = df.sample(min(500, len(df)), random_state=42)
colors_scatter = [C_RED if d else C_BLUE for d in sample["is_delinquent"]]
ax9.scatter(sample["credit_score"], sample["model_pd"] * 100,
            c=colors_scatter, alpha=0.45, s=14, edgecolors="none")
ax9.set_title("Credit Score vs Model PD Score", color=C_WHITE, fontsize=11, pad=10)
ax9.set_xlabel("Credit Score")
ax9.set_ylabel("Model PD (%)")
legend_handles = [
    plt.Line2D([0],[0], marker="o", color="w", markerfacecolor=C_BLUE, markersize=8, label="Current"),
    plt.Line2D([0],[0], marker="o", color="w", markerfacecolor=C_RED,  markersize=8, label="Delinquent"),
]
ax9.legend(handles=legend_handles, facecolor=MID_BG, labelcolor=C_WHITE, fontsize=8)

# ── Title ──────────────────────────────────────────────────────
fig.suptitle(
    "US Financial Loan Monitoring System — Portfolio Overview",
    color=C_WHITE, fontsize=17, fontweight="bold", y=0.99
)

plt.savefig(OUT_FILE, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close()
print(f"Saved: {OUT_FILE}")
