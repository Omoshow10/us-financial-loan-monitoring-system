"""
US Financial Loan Monitoring System
Script: 05_predictive_model_chart.py
Output: outputs/predictive_risk_model.png

Dashboard Page 4 — Predictive Risk Model (complete)
  - PD score distribution histogram
  - Risk band donut chart (Low / Medium / High / Critical)
  - Feature importance bar chart
  - Top 50 highest-risk loans table
  - Expected Credit Loss by risk band
  - ROC curve (best model)
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter
import warnings
warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────
BASE       = "/home/claude/us-financial-loan-monitoring"
DATA_IN    = f"{BASE}/data/processed/loan_portfolio_scored.csv"
OUT_FILE   = f"{BASE}/outputs/predictive_risk_model.png"

# ── Colours ────────────────────────────────────────────────────
DARK_BG = "#0d1b2a"
MID_BG  = "#1a3c5e"
C_BLUE  = "#2d7dd2"
C_RED   = "#e8523a"
C_AMBER = "#f39c12"
C_GREEN = "#27ae60"
C_WHITE = "#ecf0f1"
C_GREY  = "#95a5a6"

BAND_COLORS = {
    "Low":      "#27ae60",
    "Medium":   "#2d7dd2",
    "High":     "#f39c12",
    "Critical": "#e8523a",
}
BAND_ORDER = ["Low","Medium","High","Critical"]

# ── Load data ──────────────────────────────────────────────────
print("Loading data...")
df = pd.read_csv(DATA_IN)
df["expected_loss"] = df["loan_amount"] * df["model_pd"] * 0.45
df["risk_band"]     = pd.Categorical(df["risk_band"], categories=BAND_ORDER, ordered=True)
print(f"  {len(df):,} loans | avg PD: {df['model_pd'].mean():.3f}")

# ── Re-train model to get ROC curve and feature importance ─────
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, roc_auc_score

df_m = df.copy()
le = LabelEncoder()
for col in ["loan_type","borrower_segment","delinquency_status"]:
    df_m[f"{col}_enc"] = le.fit_transform(df_m[col].fillna("UNKNOWN"))

FEATURES = ["credit_score","dti_ratio","annual_income","loan_amount",
            "interest_rate","loan_term_months","loan_type_enc",
            "borrower_segment_enc","origination_year"]
TARGET = "is_default"

X = df_m[FEATURES].fillna(0)
y = (df_m["delinquency_status"].isin(["Default","Charged-Off"])).astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

scaler = StandardScaler()
X_tr_sc = scaler.fit_transform(X_train)
X_te_sc = scaler.transform(X_test)

lr = LogisticRegression(max_iter=500, class_weight="balanced", C=0.1)
lr.fit(X_tr_sc, y_train)
probs = lr.predict_proba(X_te_sc)[:, 1]
auc   = roc_auc_score(y_test, probs)
fpr, tpr, _ = roc_curve(y_test, probs)

# Feature importance (absolute coefficient)
feat_imp = pd.Series(
    np.abs(lr.coef_[0]), index=FEATURES
).sort_values(ascending=True)

# ── Aggregate stats ────────────────────────────────────────────
band_stats = df.groupby("risk_band", observed=True).agg(
    count          = ("loan_id",       "count"),
    total_balance  = ("loan_amount",   "sum"),
    avg_pd         = ("model_pd",      "mean"),
    expected_loss  = ("expected_loss", "sum"),
).reset_index()
band_stats["ecl_M"]     = band_stats["expected_loss"] / 1e6
band_stats["balance_M"] = band_stats["total_balance"]  / 1e6

total_ecl = df["expected_loss"].sum()
print(f"  Total expected credit loss: ${total_ecl/1e6:.1f}M")

# Top 50 by model_pd
top50 = df.nlargest(50, "model_pd")[
    ["loan_id","state","loan_type","credit_score","dti_ratio",
     "delinquency_status","model_pd","risk_band","expected_loss"]
].copy()
top50["dti_pct"] = (top50["dti_ratio"] * 100).round(1)
top50["pd_pct"]  = (top50["model_pd"]  * 100).round(1)
top50["ecl"]     = top50["expected_loss"].round(0)

# ── Figure ─────────────────────────────────────────────────────
fig = plt.figure(figsize=(22, 18))
fig.patch.set_facecolor(DARK_BG)
gs = gridspec.GridSpec(3, 3, figure=fig,
                       hspace=0.50, wspace=0.35,
                       height_ratios=[1.4, 1.4, 1.8])

def style_ax(ax):
    ax.set_facecolor(DARK_BG)
    for spine in ax.spines.values(): spine.set_color("#2a4a6b")
    ax.tick_params(colors=C_WHITE, labelsize=9)
    ax.xaxis.label.set_color(C_GREY)
    ax.yaxis.label.set_color(C_GREY)


# ── Panel 1: PD Score Distribution ────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
style_ax(ax1)

bins = np.linspace(0, 1, 41)
for band in BAND_ORDER:
    subset = df[df["risk_band"] == band]["model_pd"]
    ax1.hist(subset, bins=bins, alpha=0.75, color=BAND_COLORS[band],
             label=f"{band} (n={len(subset):,})", edgecolor="none")

ax1.axvline(df["model_pd"].mean(), color=C_WHITE, linestyle="--",
            linewidth=1.5, alpha=0.8,
            label=f"Mean PD: {df['model_pd'].mean():.3f}")
ax1.set_title("PD Score Distribution by Risk Band",
              color=C_WHITE, fontsize=11, pad=8)
ax1.set_xlabel("Probability of Default (model_pd)")
ax1.set_ylabel("Loan Count")
ax1.legend(facecolor=MID_BG, labelcolor=C_WHITE, fontsize=7)


# ── Panel 2: Risk Band Donut ───────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
style_ax(ax2)

counts = [band_stats.set_index("risk_band").loc[b, "count"]
          if b in band_stats["risk_band"].values else 0
          for b in BAND_ORDER]
colors = [BAND_COLORS[b] for b in BAND_ORDER]
wedges, texts, autotexts = ax2.pie(
    counts, labels=BAND_ORDER, colors=colors,
    autopct="%1.1f%%", startangle=90, pctdistance=0.78,
    wedgeprops=dict(width=0.52, edgecolor=DARK_BG, linewidth=2),
)
for t in texts:      t.set_color(C_WHITE); t.set_fontsize(9)
for t in autotexts:  t.set_color(DARK_BG);  t.set_fontsize(9); t.set_fontweight("bold")
ax2.set_title("Portfolio by Risk Band\n(Loan Count)",
              color=C_WHITE, fontsize=11, pad=8)


# ── Panel 3: ROC Curve ────────────────────────────────────────
ax3 = fig.add_subplot(gs[0, 2])
style_ax(ax3)

ax3.plot(fpr, tpr, color=C_BLUE, lw=2.5,
         label=f"Logistic Regression (AUC = {auc:.3f})")
ax3.plot([0,1],[0,1], color=C_GREY, linestyle="--", lw=1, alpha=0.5,
         label="Random classifier (AUC = 0.500)")
ax3.fill_between(fpr, tpr, alpha=0.10, color=C_BLUE)
ax3.set_title("ROC Curve — Probability of Default Model",
              color=C_WHITE, fontsize=11, pad=8)
ax3.set_xlabel("False Positive Rate")
ax3.set_ylabel("True Positive Rate (Recall)")
ax3.legend(facecolor=MID_BG, labelcolor=C_WHITE, fontsize=8)
ax3.annotate(f"AUC = {auc:.3f}", xy=(0.6, 0.2),
             color=C_BLUE, fontsize=11, fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.3", facecolor=MID_BG, alpha=0.8))


# ── Panel 4: Feature Importance ───────────────────────────────
ax4 = fig.add_subplot(gs[1, 0])
style_ax(ax4)

# Readable feature names
feat_labels = {
    "credit_score":        "Credit Score",
    "dti_ratio":           "DTI Ratio",
    "annual_income":       "Annual Income",
    "loan_amount":         "Loan Amount",
    "interest_rate":       "Interest Rate",
    "loan_term_months":    "Loan Term (months)",
    "loan_type_enc":       "Loan Type",
    "borrower_segment_enc":"Borrower Segment",
    "origination_year":    "Origination Year",
}
fi_labeled = feat_imp.rename(feat_labels)
bar_colors = [C_RED if v == fi_labeled.max() else
              C_AMBER if v >= fi_labeled.quantile(0.67) else
              C_BLUE for v in fi_labeled.values]
ax4.barh(fi_labeled.index, fi_labeled.values, color=bar_colors, edgecolor="none")
ax4.set_title("Feature Importance\n(Logistic Regression — |coefficient|)",
              color=C_WHITE, fontsize=11, pad=8)
ax4.set_xlabel("Absolute Coefficient Weight")


# ── Panel 5: Expected Credit Loss by Band ─────────────────────
ax5 = fig.add_subplot(gs[1, 1])
style_ax(ax5)

ecl_vals = [band_stats.set_index("risk_band").loc[b,"ecl_M"]
            if b in band_stats["risk_band"].values else 0
            for b in BAND_ORDER]
bars5 = ax5.bar(BAND_ORDER, ecl_vals,
                color=[BAND_COLORS[b] for b in BAND_ORDER],
                edgecolor="none", width=0.6)
for bar, val in zip(bars5, ecl_vals):
    ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
             f"${val:.1f}M", ha="center", va="bottom",
             color=C_WHITE, fontsize=9, fontweight="bold")

total_ecl_M = total_ecl / 1e6
ax5.set_title(f"Expected Credit Loss by Risk Band\n"
              f"(PD × 45% LGD × Balance)   Total: ${total_ecl_M:.1f}M",
              color=C_WHITE, fontsize=11, pad=8)
ax5.set_ylabel("Expected Loss ($M)")


# ── Panel 6: Avg PD Score by Loan Type ────────────────────────
ax6 = fig.add_subplot(gs[1, 2])
style_ax(ax6)

pd_by_type = df.groupby("loan_type")["model_pd"].mean().sort_values(ascending=True)
bar_c = [C_RED if v > df["model_pd"].mean() else C_BLUE for v in pd_by_type.values]
ax6.barh(pd_by_type.index, pd_by_type.values * 100,
         color=bar_c, edgecolor="none")
ax6.axvline(df["model_pd"].mean() * 100, color=C_AMBER,
            linestyle="--", linewidth=1.5, alpha=0.9,
            label=f"Portfolio avg {df['model_pd'].mean():.1%}")
for i, (loan_type, val) in enumerate(pd_by_type.items()):
    ax6.text(val * 100 + 0.2, i, f"{val:.1%}",
             va="center", fontsize=8, color=C_WHITE)
ax6.set_title("Average PD Score by Loan Type",
              color=C_WHITE, fontsize=11, pad=8)
ax6.set_xlabel("Average Probability of Default (%)")
ax6.legend(facecolor=MID_BG, labelcolor=C_WHITE, fontsize=8)


# ── Panel 7: Top 50 High-Risk Loans Table (spans full bottom) ─
ax7 = fig.add_subplot(gs[2, :])
ax7.set_facecolor(DARK_BG)
ax7.axis("off")

# Prepare display columns
display = top50[["loan_id","state","loan_type","credit_score",
                 "dti_pct","delinquency_status","pd_pct","risk_band","ecl"]].copy()
display.columns = ["Loan ID","State","Type","FICO","DTI %",
                   "Status","PD %","Risk Band","Exp. Loss ($)"]
display["Exp. Loss ($)"] = display["Exp. Loss ($)"].apply(lambda x: f"${x:,.0f}")
display["DTI %"]         = display["DTI %"].apply(lambda x: f"{x:.1f}%")
display["PD %"]          = display["PD %"].apply(lambda x: f"{x:.1f}%")
display = display.head(20)  # Show top 20 rows in the figure

col_widths = [0.12, 0.06, 0.10, 0.07, 0.07, 0.14, 0.07, 0.10, 0.12]
x_positions = [0.01]
for w in col_widths[:-1]:
    x_positions.append(x_positions[-1] + w)

# Header row
header_y = 0.97
for xi, (col, xp) in enumerate(zip(display.columns, x_positions)):
    ax7.text(xp, header_y, col,
             transform=ax7.transAxes,
             color=C_WHITE, fontsize=8.5, fontweight="bold",
             va="top")

# Divider line under header
ax7.plot([0.005, 0.995], [0.92, 0.92],
         color="#2a4a6b", linewidth=1,
         transform=ax7.transAxes)

# Data rows
row_height = 0.041
for ri, (_, row) in enumerate(display.iterrows()):
    y_pos = header_y - 0.07 - ri * row_height
    row_bg = "#12263a" if ri % 2 == 0 else DARK_BG
    ax7.add_patch(mpatches.FancyBboxPatch(
        (0.005, y_pos - 0.025), 0.99, row_height,
        boxstyle="square,pad=0", facecolor=row_bg,
        transform=ax7.transAxes, zorder=1
    ))
    band = row["Risk Band"]
    for xi, (val, xp) in enumerate(zip(row.values, x_positions)):
        col_name = display.columns[xi]
        colour = (BAND_COLORS.get(band, C_WHITE)
                  if col_name == "Risk Band" else C_WHITE)
        ax7.text(xp, y_pos, str(val),
                 transform=ax7.transAxes,
                 color=colour, fontsize=7.8, va="center", zorder=2)

ax7.set_title(
    f"Top 20 Highest-Risk Loans by Model PD Score  "
    f"(full watchlist: 200 loans in SQL query 04_risk_segmentation.sql)",
    color=C_WHITE, fontsize=11, pad=10
)

# ── Supertitle ─────────────────────────────────────────────────
fig.suptitle(
    "Dashboard Page 4  —  Predictive Risk Model  |  Probability of Default",
    color=C_WHITE, fontsize=16, fontweight="bold", y=0.995
)

plt.savefig(OUT_FILE, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close()
print(f"Saved: {OUT_FILE}")
