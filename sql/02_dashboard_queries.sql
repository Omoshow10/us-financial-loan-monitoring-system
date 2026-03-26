-- ============================================================
-- US Financial Loan Monitoring System
-- Script:   02_dashboard_queries.sql
-- Platform: Microsoft SQL Server 2019+
-- Tool:     SSMS or sqlcmd
-- Purpose:  All KPI and analytical queries powering the
--           four Power BI dashboard pages
--
-- Run order: After 01_create_schema.sql and 03_data_ingestion.sql
-- Usage:     Run individual query blocks as needed, or connect
--            Power BI directly via Get Data → SQL Server.
-- ============================================================

USE loan_risk_db;
GO


-- ══════════════════════════════════════════════════════════════
-- SECTION 1  |  LOAN PORTFOLIO OVERVIEW  (Dashboard Page 1)
-- ══════════════════════════════════════════════════════════════

-- KPI 1.1  Portfolio Summary — single-row scorecard
SELECT
    COUNT(*)                                                              AS total_loans,
    SUM(loan_amount)                                                      AS total_portfolio_balance,
    AVG(loan_amount)                                                      AS avg_loan_amount,
    AVG(CAST(credit_score    AS DECIMAL(8,2)))                            AS avg_credit_score,
    AVG(CAST(interest_rate   AS DECIMAL(8,4)))                            AS avg_interest_rate,
    AVG(CAST(dti_ratio       AS DECIMAL(8,4)))                            AS avg_dti_ratio,
    SUM(CASE WHEN delinquency_status <> 'Current'      THEN 1 ELSE 0 END) AS total_delinquent,
    ROUND(
        1.0 * SUM(CASE WHEN delinquency_status <> 'Current' THEN 1 ELSE 0 END)
            / COUNT(*), 4
    )                                                                     AS delinquency_rate,
    SUM(CASE WHEN delinquency_status = 'Charged-Off'   THEN 1 ELSE 0 END) AS total_charged_off,
    ROUND(
        1.0 * SUM(CASE WHEN delinquency_status = 'Charged-Off' THEN 1 ELSE 0 END)
            / COUNT(*), 4
    )                                                                     AS charge_off_rate,
    SUM(loss_given_default)                                               AS total_losses
FROM loan_portfolio;
GO


-- KPI 1.2  Loan Mix by Type
SELECT
    loan_type,
    COUNT(*)                                                              AS loan_count,
    SUM(loan_amount)                                                      AS total_balance,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)                   AS pct_of_portfolio,
    AVG(loan_amount)                                                      AS avg_balance,
    AVG(CAST(credit_score AS DECIMAL(8,2)))                               AS avg_credit_score,
    ROUND(
        1.0 * SUM(CASE WHEN delinquency_status <> 'Current' THEN 1 ELSE 0 END)
            / COUNT(*), 4
    )                                                                     AS delinquency_rate
FROM loan_portfolio
GROUP BY loan_type
ORDER BY total_balance DESC;
GO


-- KPI 1.3  Origination Volume by Year and Quarter
SELECT
    origination_year,
    origination_quarter,
    COUNT(*)                                  AS loans_originated,
    SUM(loan_amount)                          AS total_originated_balance,
    AVG(CAST(credit_score AS DECIMAL(8,2)))   AS avg_credit_score,
    AVG(CAST(interest_rate AS DECIMAL(8,4)))  AS avg_interest_rate
FROM loan_portfolio
GROUP BY origination_year, origination_quarter
ORDER BY origination_year, origination_quarter;
GO


-- ══════════════════════════════════════════════════════════════
-- SECTION 2  |  RISK INDICATORS  (Dashboard Page 2)
-- ══════════════════════════════════════════════════════════════

-- KPI 2.1  Early Delinquency Trends by Origination Year
-- 30-59 DPD is the leading indicator of portfolio stress
SELECT
    origination_year,
    loan_type,
    COUNT(*)                                                                            AS total_loans,
    SUM(CASE WHEN delinquency_status = '30-59 DPD'                   THEN 1 ELSE 0 END) AS early_delinquent,
    SUM(CASE WHEN delinquency_status IN ('60-89 DPD','90+ DPD')      THEN 1 ELSE 0 END) AS late_delinquent,
    SUM(CASE WHEN delinquency_status IN ('Default','Charged-Off')     THEN 1 ELSE 0 END) AS severe_delinquent,
    ROUND(
        1.0 * SUM(CASE WHEN delinquency_status = '30-59 DPD' THEN 1 ELSE 0 END)
            / COUNT(*), 4
    )                                                                                   AS early_delinquency_rate,
    AVG(CAST(days_past_due AS DECIMAL(8,2)))                                            AS avg_days_past_due
FROM loan_portfolio
WHERE delinquency_status <> 'Current'
GROUP BY origination_year, loan_type
ORDER BY origination_year, early_delinquency_rate DESC;
GO


-- KPI 2.2  High-Risk Borrower Segments
SELECT
    borrower_segment,
    COUNT(*)                                                              AS loan_count,
    SUM(loan_amount)                                                      AS total_exposure,
    AVG(CAST(credit_score  AS DECIMAL(8,2)))                              AS avg_credit_score,
    AVG(CAST(dti_ratio     AS DECIMAL(8,4)))                              AS avg_dti,
    AVG(CAST(annual_income AS DECIMAL(14,2)))                             AS avg_income,
    ROUND(
        1.0 * SUM(CASE WHEN delinquency_status <> 'Current' THEN 1 ELSE 0 END)
            / COUNT(*), 4
    )                                                                     AS delinquency_rate,
    ROUND(
        1.0 * SUM(CASE WHEN delinquency_status = 'Charged-Off' THEN 1 ELSE 0 END)
            / COUNT(*), 4
    )                                                                     AS charge_off_rate,
    SUM(loss_given_default)                                               AS total_lgd,
    AVG(CAST(prob_of_default AS DECIMAL(8,4)))                            AS avg_prob_default
FROM loan_portfolio
GROUP BY borrower_segment
ORDER BY delinquency_rate DESC;
GO


-- KPI 2.3  Geographic Risk Concentration — Top 20 States
SELECT TOP 20
    state,
    COUNT(*)                                                              AS total_loans,
    SUM(loan_amount)                                                      AS total_balance,
    AVG(CAST(credit_score AS DECIMAL(8,2)))                               AS avg_credit_score,
    ROUND(
        1.0 * SUM(CASE WHEN delinquency_status <> 'Current' THEN 1 ELSE 0 END)
            / COUNT(*), 4
    )                                                                     AS delinquency_rate,
    ROUND(
        1.0 * SUM(CASE WHEN delinquency_status = 'Charged-Off' THEN 1 ELSE 0 END)
            / COUNT(*), 4
    )                                                                     AS charge_off_rate,
    SUM(loss_given_default)                                               AS total_losses,
    ROUND(100.0 * SUM(loan_amount) / SUM(SUM(loan_amount)) OVER (), 2)   AS pct_portfolio
FROM loan_portfolio
GROUP BY state
ORDER BY delinquency_rate DESC;
GO


-- KPI 2.4  Delinquency Waterfall — status distribution
SELECT
    delinquency_status,
    COUNT(*)                                             AS loan_count,
    SUM(loan_amount)                                     AS total_balance,
    SUM(loss_given_default)                              AS total_lgd,
    AVG(CAST(days_past_due AS DECIMAL(8,2)))             AS avg_dpd,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)  AS pct_of_portfolio
FROM loan_portfolio
GROUP BY delinquency_status
ORDER BY
    CASE delinquency_status
        WHEN 'Current'     THEN 1
        WHEN '30-59 DPD'   THEN 2
        WHEN '60-89 DPD'   THEN 3
        WHEN '90+ DPD'     THEN 4
        WHEN 'Default'     THEN 5
        WHEN 'Charged-Off' THEN 6
    END;
GO


-- KPI 2.5  Credit Score Band vs Delinquency Rate
SELECT
    CASE
        WHEN credit_score BETWEEN 300 AND 579 THEN '300-579  Poor'
        WHEN credit_score BETWEEN 580 AND 669 THEN '580-669  Fair'
        WHEN credit_score BETWEEN 670 AND 739 THEN '670-739  Good'
        WHEN credit_score BETWEEN 740 AND 799 THEN '740-799  Very Good'
        ELSE                                       '800-850  Exceptional'
    END                                                                   AS credit_band,
    COUNT(*)                                                              AS loan_count,
    SUM(loan_amount)                                                      AS total_balance,
    ROUND(
        1.0 * SUM(CASE WHEN delinquency_status <> 'Current' THEN 1 ELSE 0 END)
            / COUNT(*), 4
    )                                                                     AS delinquency_rate,
    AVG(CAST(prob_of_default AS DECIMAL(8,4)))                            AS avg_prob_default,
    SUM(loss_given_default)                                               AS total_losses
FROM loan_portfolio
GROUP BY
    CASE
        WHEN credit_score BETWEEN 300 AND 579 THEN '300-579  Poor'
        WHEN credit_score BETWEEN 580 AND 669 THEN '580-669  Fair'
        WHEN credit_score BETWEEN 670 AND 739 THEN '670-739  Good'
        WHEN credit_score BETWEEN 740 AND 799 THEN '740-799  Very Good'
        ELSE                                       '800-850  Exceptional'
    END
ORDER BY credit_band;
GO


-- ══════════════════════════════════════════════════════════════
-- SECTION 3  |  RISK CONCENTRATION  (Dashboard Page 3)
-- ══════════════════════════════════════════════════════════════

-- KPI 3.1  High-Concentration States — flags states with
--          delinquency rate above 1.5x the national average
WITH national_avg AS (
    SELECT ROUND(
        1.0 * SUM(CASE WHEN delinquency_status <> 'Current' THEN 1 ELSE 0 END)
            / COUNT(*), 4
    ) AS nat_delinquency_rate
    FROM loan_portfolio
),
state_risk AS (
    SELECT
        state,
        COUNT(*)         AS loan_count,
        SUM(loan_amount) AS total_balance,
        ROUND(
            1.0 * SUM(CASE WHEN delinquency_status <> 'Current' THEN 1 ELSE 0 END)
                / COUNT(*), 4
        )                AS delinquency_rate
    FROM loan_portfolio
    GROUP BY state
)
SELECT
    sr.state,
    sr.loan_count,
    sr.total_balance,
    sr.delinquency_rate,
    na.nat_delinquency_rate,
    ROUND(sr.delinquency_rate / na.nat_delinquency_rate, 2) AS risk_multiplier,
    CASE
        WHEN sr.delinquency_rate > na.nat_delinquency_rate * 2.0 THEN 'CRITICAL'
        WHEN sr.delinquency_rate > na.nat_delinquency_rate * 1.5 THEN 'HIGH'
        WHEN sr.delinquency_rate > na.nat_delinquency_rate * 1.0 THEN 'ELEVATED'
        ELSE 'NORMAL'
    END AS risk_flag
FROM state_risk sr
CROSS JOIN national_avg na
ORDER BY risk_multiplier DESC;
GO


-- KPI 3.2  Loan Type × Borrower Segment Risk Matrix
SELECT
    loan_type,
    borrower_segment,
    COUNT(*)                                                             AS loan_count,
    ROUND(AVG(loan_amount), 0)                                           AS avg_balance,
    ROUND(
        1.0 * SUM(CASE WHEN delinquency_status <> 'Current' THEN 1 ELSE 0 END)
            / COUNT(*), 4
    )                                                                    AS delinquency_rate,
    ROUND(AVG(CAST(prob_of_default AS DECIMAL(8,4))), 4)                 AS avg_pd,
    ROUND(SUM(loss_given_default) / NULLIF(SUM(loan_amount), 0), 4)     AS loss_rate
FROM loan_portfolio
GROUP BY loan_type, borrower_segment
ORDER BY delinquency_rate DESC;
GO


-- KPI 3.3  Expected Loss by Segment — Top 20
SELECT TOP 20
    borrower_segment,
    loan_type,
    COUNT(*)                                           AS loans,
    SUM(loan_amount)                                   AS total_exposure,
    AVG(CAST(prob_of_default AS DECIMAL(8,4)))         AS avg_pd,
    SUM(loss_given_default)                            AS realized_lgd,
    ROUND(SUM(loan_amount * prob_of_default), 0)       AS expected_loss_estimate
FROM loan_portfolio
GROUP BY borrower_segment, loan_type
ORDER BY expected_loss_estimate DESC;
GO
