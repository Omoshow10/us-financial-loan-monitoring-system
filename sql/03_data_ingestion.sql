-- ============================================================
-- US Financial Loan Monitoring System
-- Script 03: Data Ingestion — Load CSV into SQL Tables
-- ============================================================
-- Run after: 01_create_schema.sql
-- Requires:  data/processed/loan_portfolio_scored.csv

-- ── PostgreSQL COPY method ─────────────────────────────────────
-- Update the path below to match your local file location.

\COPY loan_portfolio (
    loan_id, origination_date, state, loan_type, loan_amount,
    interest_rate, loan_term_months, credit_score, annual_income,
    dti_ratio, borrower_segment, delinquency_status, days_past_due,
    loss_given_default, prob_of_default, origination_year, origination_quarter
)
FROM '/path/to/us-financial-loan-monitoring/data/processed/loan_portfolio.csv'
WITH (FORMAT CSV, HEADER TRUE, NULL '');

-- Load ML risk scores
\COPY loan_risk_scores (loan_id, model_pd, risk_band)
FROM '/path/to/us-financial-loan-monitoring/data/processed/loan_portfolio_scored.csv'
WITH (FORMAT CSV, HEADER TRUE, NULL '');

-- Update score metadata
UPDATE loan_risk_scores
SET score_date    = CURRENT_DATE,
    model_version = 'GBM_v1.0'
WHERE score_date IS NULL;


-- ── SQL Server BULK INSERT method (alternative) ────────────────
/*
BULK INSERT loan_portfolio
FROM 'C:\path\to\loan_portfolio.csv'
WITH (
    FORMAT = 'CSV',
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);
*/


-- ── Populate delinquency_history from loaded data ─────────────
INSERT INTO delinquency_history (
    snapshot_month,
    total_loans,
    delinquent_loans,
    avg_credit_score,
    total_balance,
    delinquency_rate
)
SELECT
    origination_quarter                                 AS snapshot_month,
    COUNT(*)                                            AS total_loans,
    SUM(CASE WHEN delinquency_status <> 'Current'
             THEN 1 ELSE 0 END)                        AS delinquent_loans,
    ROUND(AVG(credit_score::NUMERIC), 2)                AS avg_credit_score,
    SUM(loan_amount)                                    AS total_balance,
    ROUND(
        SUM(CASE WHEN delinquency_status <> 'Current'
                 THEN 1 ELSE 0 END)::NUMERIC
        / NULLIF(COUNT(*), 0), 4
    )                                                   AS delinquency_rate
FROM loan_portfolio
GROUP BY origination_quarter
ORDER BY origination_quarter;


-- ── Verification counts ────────────────────────────────────────
SELECT 'loan_portfolio'    AS table_name, COUNT(*) AS row_count FROM loan_portfolio
UNION ALL
SELECT 'loan_risk_scores'  AS table_name, COUNT(*) AS row_count FROM loan_risk_scores
UNION ALL
SELECT 'delinquency_history' AS table_name, COUNT(*) AS row_count FROM delinquency_history;
