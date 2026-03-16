# Risk Metrics Methodology
## US Financial Loan Monitoring System

This document explains the risk metrics used in the dashboard, their regulatory basis, and how they are calculated.

---

## 1. Delinquency Rate

**Definition:** The percentage of loans in the portfolio that have missed one or more scheduled payments.

**Formula:**
```
Delinquency Rate (30+) = Loans with DPD ≥ 30 / Total Active Loans × 100
```

**Regulatory Context:**
- The FFIEC (Federal Financial Institutions Examination Council) requires banks to report delinquencies at 30, 60, and 90-day buckets
- The FDIC Uniform Bank Performance Report (UBPR) tracks delinquency ratios quarterly
- The Federal Reserve's Senior Loan Officer Opinion Survey (SLOOS) monitors delinquency trends at the macro level

**Interpretation:**
| Rate | Signal |
|------|--------|
| < 2% | Excellent portfolio health |
| 2–4% | Normal range for diversified portfolio |
| 4–6% | Elevated; warrants management attention |
| > 6% | High risk; potential regulatory scrutiny |

---

## 2. Non-Performing Loan (NPL) Rate

**Definition:** The percentage of loans classified as non-performing (90+ days past due or in non-accrual status).

**Formula:**
```
NPL Rate = Loans with DPD ≥ 90 / Total Active Loans × 100
```

**Regulatory Context:**
- Loans 90+ DPD are typically placed on **non-accrual status** under US GAAP — the bank stops recognizing interest income
- The OCC and FDIC use NPL ratio as a primary credit quality indicator in bank examinations
- Basel III uses 90-DPD as the default trigger in probability of default (PD) models

---

## 3. Charge-Off Rate

**Definition:** The rate at which loans are written off as unrecoverable losses, net of recoveries.

**Formulas:**
```
Gross Charge-Off Rate = Gross Charge-Offs / Average Loan Balance × 100

Net Charge-Off Rate   = (Gross Charge-Offs - Recoveries) / Average Loan Balance × 100
```

**Regulatory Context:**
- US banks report charge-offs quarterly in the FFIEC Call Report (Schedule RI-B)
- The Federal Reserve tracks aggregate net charge-off rates by loan type in the G.19 and H.8 statistical releases
- Credit card NCO rates are typically 3–5× higher than mortgage NCO rates

**Industry Benchmarks (approximate):**
| Product | Typical NCO Range |
|---------|------------------|
| Mortgages | 0.05% – 0.30% |
| Auto | 0.50% – 1.50% |
| Personal Loans | 1.50% – 4.00% |
| Credit Cards | 2.50% – 6.00% |

---

## 4. Loan-to-Value (LTV) Ratio

**Definition:** The ratio of the loan balance to the appraised value of the collateral.

**Formula:**
```
LTV = Current Loan Balance / Current Collateral Value × 100
```

**Significance:**
- LTV > 80% typically requires Private Mortgage Insurance (PMI) for conventional mortgages
- LTV > 100% ("underwater" loan) is a leading predictor of strategic default
- The OCC's Guidance on Credit Risk specifies LTV limits by property type

---

## 5. Debt-to-Income (DTI) Ratio

**Definition:** The borrower's total monthly debt obligations as a percentage of gross monthly income.

**Formula:**
```
DTI = Total Monthly Debt Payments / Gross Monthly Income × 100
```

**Regulatory Thresholds:**
| DTI | Qualification Status |
|-----|---------------------|
| < 28% | Front-end: Mortgage payment only (housing ratio) |
| < 36% | Preferred threshold for conventional loans |
| < 43% | CFPB Qualified Mortgage (QM) maximum |
| > 43% | Non-QM / higher risk; restricted products |

---

## 6. FICO Score Tiers

**Definition:** Credit score (300–850) assigned by FICO based on credit bureau data.

| FICO Range | Tier | Typical Lending Treatment |
|------------|------|--------------------------|
| 740–850 | Super-Prime | Best rates; broadest product access |
| 680–739 | Prime | Standard market rates |
| 620–679 | Near-Prime | Slightly elevated rates; some restrictions |
| 580–619 | Subprime | Significantly elevated rates; FHA eligible |
| < 580 | Deep Subprime | Very limited access; specialty lenders only |

---

## 7. Probability of Default (PD) Model

**Definition:** A statistical model that estimates the probability that a borrower will default within the next 12 months.

**Methodology:**
This project trains three models using supervised machine learning:

1. **Logistic Regression** — Interpretable baseline; coefficients directly map to credit scorecard weights
2. **Random Forest** — Ensemble method capturing non-linear relationships (e.g., FICO × DTI interaction)
3. **XGBoost** — Gradient boosted trees; typically highest accuracy for tabular financial data

**Feature Set:**
| Feature | Direction | Rationale |
|---------|-----------|-----------|
| FICO Score | ↓ Higher = lower PD | Primary predictor in all credit models |
| Debt-to-Income | ↑ Higher = higher PD | Cash flow stress indicator |
| Loan-to-Value | ↑ Higher = higher PD | Collateral adequacy |
| Employment Status | Varies | Income stability |
| Derogatory Marks | ↑ Higher = higher PD | Prior credit distress |
| Loan Age (Months) | Varies | Vintage/seasoning effect |
| Prior Delinquency | ↑ Higher = higher PD | Strongest behavioral predictor |

**Model Evaluation:**
- Primary metric: **ROC-AUC** (Area Under the ROC Curve) — industry standard for credit models
- Target: AUC > 0.80 for production-quality credit risk model
- Benchmark: FICO Score alone typically achieves AUC ≈ 0.72–0.76

**Basel III PD Framework:**
Under Basel III's Internal Ratings-Based (IRB) approach:
- PD × LGD × EAD = Expected Loss (EL)
- LGD (Loss Given Default): ~45% for unsecured, ~25% for secured consumer
- EAD (Exposure at Default): Current outstanding balance for term loans

---

## 8. Geographic Concentration Risk

**Definition:** The degree to which a loan portfolio is concentrated in specific geographic markets, creating correlated risk.

**Why It Matters:**
- Geographic concentration means a regional recession, natural disaster, or real estate market downturn can simultaneously impact a large portion of the portfolio
- The OCC's Large Bank Supervision handbook explicitly flags geographic concentration as a key credit risk factor
- Post-2008, regulators increased scrutiny of banks with >25% exposure to single states

**Concentration Thresholds Used:**
| Concentration | Alert Level |
|---------------|-------------|
| > 25% in single state | 🔴 CRITICAL |
| 15–25% in single state | 🟠 HIGH |
| 10–15% in single state | 🟡 ELEVATED |
| < 10% | 🟢 Normal |

---

## 9. Vintage Analysis

**Definition:** Analysis of loan cohorts by origination period to track how default rates evolve over the life of a loan.

**How to Read a Vintage Chart:**
- X-axis: Loan age (months since origination)
- Y-axis: Cumulative default rate
- Each line: A cohort of loans originated in the same period (month/quarter/year)

**Key Observations:**
- **Early Default Rate:** Defaults in months 0–12 indicate underwriting quality issues
- **Peak Default Window:** Consumer loans typically peak defaults at 18–36 months of age
- **Worsening Vintages:** If recent cohorts are defaulting faster than older ones, underwriting standards have loosened
