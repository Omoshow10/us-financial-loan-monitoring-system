"""
risk_model.py
─────────────
US Financial Loan Monitoring System
Step 2 of 2: Exploratory Data Analysis + Probability of Default Model

Usage:
    python python/risk_model.py

Outputs:
    outputs/eda_charts.png
    outputs/model_performance.png
    outputs/feature_importance.png
    data/processed/loan_portfolio_scored.csv
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, roc_curve, precision_recall_curve,
    average_precision_score
)
import warnings
warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = "/home/claude/us-financial-loan-monitoring"
DATA_IN  = f"{BASE}/data/processed/loan_portfolio.csv"
DATA_OUT = f"{BASE}/data/processed/loan_portfolio_scored.csv"
OUT_DIR  = f"{BASE}/outputs"

# ══════════════════════════════════════════════════════════════════════════════
# 1. LOAD & PREP
# ══════════════════════════════════════════════════════════════════════════════
print("Loading data...")
df = pd.read_csv(DATA_IN, parse_dates=["origination_date"])

# Binary target: 1 = defaulted or charged-off
df["is_default"] = df["delinquency_status"].isin(["Default","Charged-Off"]).astype(int)
df["is_delinquent"] = (df["delinquency_status"] != "Current").astype(int)

print(f"  Records     : {len(df):,}")
print(f"  Default rate: {df['is_default'].mean():.2%}")
print(f"  Delinq rate : {df['is_delinquent'].mean():.2%}")

# ══════════════════════════════════════════════════════════════════════════════
# 2. EDA CHARTS (4-panel)
# ══════════════════════════════════════════════════════════════════════════════
print("\nGenerating EDA charts...")

COLORS = {
    "primary":   "#1a3c5e",
    "secondary": "#e8523a",
    "accent":    "#2ecc71",
    "warn":      "#f39c12",
    "light":     "#ecf0f1",
    "mid":       "#95a5a6",
}
SEG_ORDER = ["Deep Subprime","Subprime","Near-Prime","Prime"]
STATUS_ORDER = ["Current","30-59 DPD","60-89 DPD","90+ DPD","Default","Charged-Off"]

fig = plt.figure(figsize=(18, 14))
fig.patch.set_facecolor("#0d1b2a")
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

# Panel 1 ─ Delinquency by Loan Type
ax1 = fig.add_subplot(gs[0, 0])
delq_by_type = (
    df.groupby("loan_type")["is_delinquent"]
    .mean()
    .sort_values(ascending=True) * 100
)
colors_bar = [COLORS["secondary"] if v > delq_by_type.mean() else COLORS["primary"]
              for v in delq_by_type]
bars = ax1.barh(delq_by_type.index, delq_by_type.values, color=colors_bar, edgecolor="none")
for bar, val in zip(bars, delq_by_type.values):
    ax1.text(val + 0.3, bar.get_y() + bar.get_height()/2,
             f"{val:.1f}%", va="center", ha="left",
             color="white", fontsize=9)
ax1.axvline(delq_by_type.mean(), color=COLORS["warn"], linestyle="--", linewidth=1.2, alpha=0.8)
ax1.set_title("Delinquency Rate by Loan Type", color="white", fontsize=11, pad=10)
ax1.set_xlabel("Delinquency Rate (%)", color=COLORS["mid"])
ax1.tick_params(colors="white")
ax1.set_facecolor("#0d1b2a")
for spine in ax1.spines.values(): spine.set_color("#2a4a6b")

# Panel 2 ─ Credit Score Distribution
ax2 = fig.add_subplot(gs[0, 1])
ax2.hist(df[df["is_default"]==0]["credit_score"], bins=40, alpha=0.7,
         color=COLORS["primary"], label="Performing", edgecolor="none")
ax2.hist(df[df["is_default"]==1]["credit_score"], bins=40, alpha=0.8,
         color=COLORS["secondary"], label="Default/Charged-Off", edgecolor="none")
ax2.set_title("Credit Score: Performing vs Defaulted", color="white", fontsize=11, pad=10)
ax2.set_xlabel("Credit Score", color=COLORS["mid"])
ax2.set_ylabel("Loan Count", color=COLORS["mid"])
ax2.tick_params(colors="white")
ax2.set_facecolor("#0d1b2a")
ax2.legend(facecolor="#1a3c5e", labelcolor="white", framealpha=0.8, fontsize=8)
for spine in ax2.spines.values(): spine.set_color("#2a4a6b")

# Panel 3 ─ DTI vs Default Rate (scatter)
ax3 = fig.add_subplot(gs[0, 2])
dti_bins = pd.cut(df["dti_ratio"], bins=10)
dti_risk  = df.groupby(dti_bins, observed=True)["is_default"].mean() * 100
mid_pts   = [iv.mid for iv in dti_risk.index]
ax3.bar(mid_pts, dti_risk.values, width=0.06,
        color=COLORS["warn"], edgecolor="none", alpha=0.85)
ax3.set_title("Default Rate by DTI Ratio", color="white", fontsize=11, pad=10)
ax3.set_xlabel("Debt-to-Income Ratio", color=COLORS["mid"])
ax3.set_ylabel("Default Rate (%)", color=COLORS["mid"])
ax3.tick_params(colors="white")
ax3.set_facecolor("#0d1b2a")
for spine in ax3.spines.values(): spine.set_color("#2a4a6b")

# Panel 4 ─ Borrower Segment Risk
ax4 = fig.add_subplot(gs[1, 0])
seg_risk = (
    df.groupby("borrower_segment")[["is_delinquent","is_default"]]
    .mean() * 100
).reindex(SEG_ORDER)
x = np.arange(len(SEG_ORDER))
w = 0.35
ax4.bar(x - w/2, seg_risk["is_delinquent"], width=w,
        color=COLORS["warn"], label="Delinquency Rate", edgecolor="none")
ax4.bar(x + w/2, seg_risk["is_default"], width=w,
        color=COLORS["secondary"], label="Default Rate", edgecolor="none")
ax4.set_xticks(x)
ax4.set_xticklabels(SEG_ORDER, rotation=12, ha="right", fontsize=8, color="white")
ax4.set_title("Risk by Borrower Segment", color="white", fontsize=11, pad=10)
ax4.set_ylabel("Rate (%)", color=COLORS["mid"])
ax4.tick_params(colors="white")
ax4.set_facecolor("#0d1b2a")
ax4.legend(facecolor="#1a3c5e", labelcolor="white", framealpha=0.8, fontsize=8)
for spine in ax4.spines.values(): spine.set_color("#2a4a6b")

# Panel 5 ─ Portfolio Delinquency Status Waterfall
ax5 = fig.add_subplot(gs[1, 1])
status_counts = df["delinquency_status"].value_counts().reindex(STATUS_ORDER, fill_value=0)
bar_colors = [COLORS["primary"], COLORS["warn"], "#e67e22",
              COLORS["secondary"], "#c0392b", "#7f8c8d"]
bars5 = ax5.bar(STATUS_ORDER, status_counts.values, color=bar_colors, edgecolor="none")
for bar, val in zip(bars5, status_counts.values):
    ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
             f"{val:,}", ha="center", va="bottom", color="white", fontsize=8)
ax5.set_title("Portfolio Delinquency Waterfall", color="white", fontsize=11, pad=10)
ax5.set_ylabel("Loan Count", color=COLORS["mid"])
ax5.tick_params(colors="white")
plt.setp(ax5.get_xticklabels(), rotation=25, ha="right", fontsize=8)
ax5.set_facecolor("#0d1b2a")
for spine in ax5.spines.values(): spine.set_color("#2a4a6b")

# Panel 6 ─ Top 10 States by Delinquency
ax6 = fig.add_subplot(gs[1, 2])
top_states = (
    df.groupby("state")["is_delinquent"]
    .mean()
    .sort_values(ascending=False)
    .head(10) * 100
)
bar_c = [COLORS["secondary"] if v > top_states.mean() else COLORS["warn"]
         for v in top_states.values]
ax6.bar(top_states.index, top_states.values, color=bar_c, edgecolor="none")
ax6.set_title("Top 10 States: Delinquency Rate", color="white", fontsize=11, pad=10)
ax6.set_ylabel("Delinquency Rate (%)", color=COLORS["mid"])
ax6.tick_params(colors="white")
ax6.set_facecolor("#0d1b2a")
for spine in ax6.spines.values(): spine.set_color("#2a4a6b")

fig.suptitle("US Loan Portfolio — Exploratory Risk Analysis",
             color="white", fontsize=16, fontweight="bold", y=0.98)
plt.savefig(f"{OUT_DIR}/eda_charts.png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
plt.close()
print("  Saved: eda_charts.png")

# ══════════════════════════════════════════════════════════════════════════════
# 3. PREDICTIVE MODEL ─ Probability of Default
# ══════════════════════════════════════════════════════════════════════════════
print("\nTraining default prediction model...")

# Feature engineering
df_model = df.copy()
le = LabelEncoder()
df_model["loan_type_enc"]     = le.fit_transform(df_model["loan_type"])
df_model["state_enc"]         = le.fit_transform(df_model["state"])
df_model["segment_enc"]       = le.fit_transform(df_model["borrower_segment"])

FEATURES = [
    "credit_score", "dti_ratio", "annual_income", "loan_amount",
    "interest_rate", "loan_term_months", "loan_type_enc",
    "state_enc", "segment_enc", "origination_year"
]
TARGET = "is_default"

X = df_model[FEATURES].fillna(0)
y = df_model[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

# Train three models
models = {
    "Logistic Regression": LogisticRegression(max_iter=500, class_weight="balanced"),
    "Random Forest":        RandomForestClassifier(n_estimators=200, max_depth=8,
                                                    class_weight="balanced", random_state=42),
    "Gradient Boosting":   GradientBoostingClassifier(n_estimators=200, max_depth=4,
                                                       learning_rate=0.05, random_state=42),
}

results = {}
for name, model in models.items():
    Xtr = X_train_sc if name == "Logistic Regression" else X_train
    Xte = X_test_sc  if name == "Logistic Regression" else X_test
    model.fit(Xtr, y_train)
    probs = model.predict_proba(Xte)[:, 1]
    auc   = roc_auc_score(y_test, probs)
    ap    = average_precision_score(y_test, probs)
    results[name] = {"model": model, "probs": probs, "auc": auc, "ap": ap}
    print(f"  {name:25s} AUC={auc:.4f}  AP={ap:.4f}")

# Best model = GBM (typically)
best_name  = max(results, key=lambda k: results[k]["auc"])
best_model = results[best_name]["model"]
print(f"\n  Best model: {best_name}")

# ── Model Performance Plot ────────────────────────────────────────────────────
fig2, axes = plt.subplots(1, 3, figsize=(18, 5))
fig2.patch.set_facecolor("#0d1b2a")

# ROC curves
ax = axes[0]
ax.set_facecolor("#0d1b2a")
for spine in ax.spines.values(): spine.set_color("#2a4a6b")
plot_colors = [COLORS["primary"], COLORS["warn"], COLORS["secondary"]]
for (name, r), col in zip(results.items(), plot_colors):
    fpr, tpr, _ = roc_curve(y_test, r["probs"])
    ax.plot(fpr, tpr, color=col, lw=2, label=f"{name} (AUC={r['auc']:.3f})")
ax.plot([0,1],[0,1], "w--", lw=1, alpha=0.4)
ax.set_xlabel("False Positive Rate", color=COLORS["mid"])
ax.set_ylabel("True Positive Rate", color=COLORS["mid"])
ax.set_title("ROC Curves — All Models", color="white", fontsize=11)
ax.legend(facecolor="#1a3c5e", labelcolor="white", fontsize=8)
ax.tick_params(colors="white")

# Confusion matrix (best model)
ax = axes[1]
ax.set_facecolor("#0d1b2a")
Xte_best = X_test_sc if best_name == "Logistic Regression" else X_test
cm = confusion_matrix(y_test, best_model.predict(Xte_best))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=["Performing","Default"],
            yticklabels=["Performing","Default"],
            ax=ax, cbar=False)
ax.set_title(f"Confusion Matrix\n{best_name}", color="white", fontsize=11)
ax.tick_params(colors="white")
ax.set_xlabel("Predicted", color=COLORS["mid"])
ax.set_ylabel("Actual",    color=COLORS["mid"])

# Feature importance
ax = axes[2]
ax.set_facecolor("#0d1b2a")
for spine in ax.spines.values(): spine.set_color("#2a4a6b")
if hasattr(best_model, "feature_importances_"):
    fi = pd.Series(best_model.feature_importances_, index=FEATURES).sort_values()
    ax.barh(fi.index, fi.values, color=COLORS["warn"], edgecolor="none")
    ax.set_title("Feature Importance (Best Model)", color="white", fontsize=11)
    ax.set_xlabel("Importance", color=COLORS["mid"])
    ax.tick_params(colors="white")

fig2.suptitle("Probability of Default — Model Performance",
              color="white", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/model_performance.png", dpi=150, bbox_inches="tight",
            facecolor=fig2.get_facecolor())
plt.close()
print("  Saved: model_performance.png")

# ── Score all loans and save ──────────────────────────────────────────────────
X_all    = df_model[FEATURES].fillna(0)
X_all_sc = scaler.transform(X_all)
Xfull    = X_all_sc if best_name == "Logistic Regression" else X_all

df["model_pd"] = best_model.predict_proba(Xfull)[:, 1].round(4)
df["risk_band"] = pd.cut(
    df["model_pd"],
    bins=[0, 0.05, 0.15, 0.30, 1.0],
    labels=["Low","Medium","High","Critical"]
)
df.to_csv(DATA_OUT, index=False)
print(f"  Saved: loan_portfolio_scored.csv ({len(df):,} rows)")
print("\nRisk Band Distribution:")
print(df["risk_band"].value_counts().sort_index().to_string())
print("\nDone ✅")
