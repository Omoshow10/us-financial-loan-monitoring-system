# Power BI Dashboard — Setup Guide
## US Financial Loan Monitoring System

---

## Step 1: Import Data

Open Power BI Desktop → **Home → Get Data → Text/CSV**

Import these four files from `data/processed/`:

| File | Table Name |
|------|-----------|
| `loan_portfolio_scored.csv` | `LoanPortfolio` |
| `delinquency_trends.csv` | `DelinquencyTrends` |
| `geographic_risk.csv` | `GeographicRisk` |
| `borrower_segments.csv` | `BorrowerSegments` |

---

## Step 2: Data Types

In **Power Query Editor**, confirm these column types for `LoanPortfolio`:

| Column | Type |
|--------|------|
| `origination_date` | Date |
| `loan_amount` | Decimal Number |
| `interest_rate` | Decimal Number |
| `credit_score` | Whole Number |
| `dti_ratio` | Decimal Number |
| `days_past_due` | Whole Number |
| `loss_given_default` | Decimal Number |
| `prob_of_default` | Decimal Number |
| `model_pd` | Decimal Number |

---

## Step 3: Relationships

In **Model View**, create these relationships:

```
LoanPortfolio[state] → GeographicRisk[state]        (Many-to-One)
LoanPortfolio[borrower_segment] → BorrowerSegments[borrower_segment] (Many-to-One)
```

---

## Step 4: DAX Measures

Create a **Measures Table** (Enter Data → empty table named `_Measures`), then add:

### Portfolio Overview KPIs

```dax
Total Loans = COUNTROWS(LoanPortfolio)

Total Portfolio Balance = SUM(LoanPortfolio[loan_amount])

Avg Loan Amount = AVERAGE(LoanPortfolio[loan_amount])

Avg Credit Score = AVERAGE(LoanPortfolio[credit_score])

Avg Interest Rate = AVERAGE(LoanPortfolio[interest_rate])
```

### Delinquency Metrics

```dax
Total Delinquent Loans =
CALCULATE(
    COUNTROWS(LoanPortfolio),
    LoanPortfolio[delinquency_status] <> "Current"
)

Delinquency Rate =
DIVIDE(
    [Total Delinquent Loans],
    [Total Loans],
    0
)

Delinquency Rate % = FORMAT([Delinquency Rate], "0.00%")

Early Delinquency (30-59 DPD) =
CALCULATE(
    COUNTROWS(LoanPortfolio),
    LoanPortfolio[delinquency_status] = "30-59 DPD"
)

Early Delinquency Rate =
DIVIDE(
    [Early Delinquency (30-59 DPD)],
    [Total Loans],
    0
)
```

### Charge-Off Metrics

```dax
Total Charged Off =
CALCULATE(
    COUNTROWS(LoanPortfolio),
    LoanPortfolio[delinquency_status] = "Charged-Off"
)

Charge-Off Rate =
DIVIDE(
    [Total Charged Off],
    [Total Loans],
    0
)

Total Losses (LGD) = SUM(LoanPortfolio[loss_given_default])

Loss Rate =
DIVIDE(
    [Total Losses (LGD)],
    [Total Portfolio Balance],
    0
)
```

### Predictive Risk

```dax
Avg Probability of Default = AVERAGE(LoanPortfolio[model_pd])

High Risk Loans =
CALCULATE(
    COUNTROWS(LoanPortfolio),
    LoanPortfolio[risk_band] IN {"High", "Critical"}
)

High Risk Exposure =
CALCULATE(
    SUM(LoanPortfolio[loan_amount]),
    LoanPortfolio[risk_band] IN {"High", "Critical"}
)

Expected Loss =
SUMX(
    LoanPortfolio,
    LoanPortfolio[loan_amount] * LoanPortfolio[model_pd]
)
```

### Conditional Formatting Helpers

```dax
Delinquency Rate Color =
SWITCH(
    TRUE(),
    [Delinquency Rate] > 0.25, "Red",
    [Delinquency Rate] > 0.15, "Orange",
    [Delinquency Rate] > 0.08, "Yellow",
    "Green"
)

Risk Score Label =
SWITCH(
    TRUE(),
    [Avg Probability of Default] > 0.30, "🔴 Critical",
    [Avg Probability of Default] > 0.15, "🟠 High",
    [Avg Probability of Default] > 0.05, "🟡 Medium",
    "🟢 Low"
)
```

---

## Step 5: Dashboard Pages

### Page 1 - Portfolio Overview

**Visuals:**
- 5 KPI cards (top row): Total Loans, Total Balance, Avg Credit Score, Delinquency Rate %, Charge-Off Rate
- Donut chart: Loan Mix by Type (loan_type, count)
- Clustered bar: Balance by Origination Year
- Line chart: Monthly origination volume (use `DelinquencyTrends[month]`)
- Table: Top 10 states by balance

### Page 2 - Risk Indicators

**Visuals:**
- KPI cards: Early Delinquency Rate, 90+ DPD Rate, Avg DTI, Avg PD
- Waterfall / stacked bar: Delinquency status progression
- Line chart: Early delinquency trend over time (`DelinquencyTrends`)
- Clustered bar: Delinquency Rate by Borrower Segment
- Scatter plot: Credit Score vs Probability of Default (credit_score x-axis, model_pd y-axis, loan_amount as bubble size)

### Page 3 - Geographic Risk

**Visuals:**
- Filled map: State → color by `delinquency_rate` (use `GeographicRisk` table)
- Treemap: State → total_balance, colored by risk_tier
- Bar chart: Top 15 states by delinquency rate
- Table: State risk scorecard (state, total_loans, delinquency_rate, charge_off_rate, avg_credit_score, risk_tier)

### Page 4 - Predictive Model

**Visuals:**
- KPI: Expected Loss ($), Avg PD %, High Risk Loan Count
- Donut: Risk Band Distribution (risk_band, count)
- Scatter: model_pd vs credit_score
- Bar: Avg PD by Borrower Segment + Loan Type
- Table: Top 50 highest-risk loans (loan_id, state, loan_type, credit_score, dti_ratio, model_pd, risk_band)

---

## Step 6: Slicers (apply to all pages)

Add these slicers to a **sync panel** (View → Sync Slicers):

- `loan_type` (multi-select list)
- `borrower_segment` (multi-select list)  
- `origination_year` (slider or dropdown)
- `state` (dropdown)
- `risk_band` (button slicer)

---

## Step 7: Conditional Formatting

Apply to the State Risk Table:
- `delinquency_rate` column → Background color scale: Green (0%) → Red (30%+)
- `risk_tier` column → Rules: Low=Green, Moderate=Yellow, High=Orange, Critical=Red

---

## Theme Colors

```json
{
    "name": "LoanRisk",
    "dataColors": ["#1a3c5e","#e8523a","#f39c12","#2ecc71","#95a5a6","#3498db"],
    "background": "#ffffff",
    "foreground": "#0d1b2a",
    "tableAccent": "#1a3c5e"
}
```

Save as `powerbi/LoanRisk_theme.json` and apply via **View → Themes → Browse for themes**.
