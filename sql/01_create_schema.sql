-- ============================================================
-- US Financial Loan Monitoring System
-- Script:   01_create_schema.sql
-- Platform: Microsoft SQL Server 2019+
-- Tool:     SQL Server Management Studio (SSMS) or sqlcmd
-- Purpose:  Create database, tables, constraints, and indexes
--
-- Run order: This script must run FIRST before any other script.
-- ============================================================

-- ── Step 1: Create the database (run once) ────────────────────
-- Run this block separately in SSMS if the database does not
-- exist yet. Comment it out on subsequent runs.
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'loan_risk_db')
BEGIN
    CREATE DATABASE loan_risk_db;
END
GO

USE loan_risk_db;
GO


-- ── Step 2: Drop existing tables (safe re-run) ───────────────
-- Order matters: drop child tables before parent tables.
IF OBJECT_ID('loan_risk_scores',   'U') IS NOT NULL DROP TABLE loan_risk_scores;
IF OBJECT_ID('delinquency_history','U') IS NOT NULL DROP TABLE delinquency_history;
IF OBJECT_ID('loan_portfolio',     'U') IS NOT NULL DROP TABLE loan_portfolio;
GO


-- ── Step 3: Create tables ─────────────────────────────────────

-- TABLE 1: loan_portfolio
-- Core fact table — one row per loan
CREATE TABLE loan_portfolio (
    loan_id              VARCHAR(10)    NOT NULL,
    origination_date     DATE           NOT NULL,
    state                CHAR(2)        NOT NULL,
    loan_type            VARCHAR(20)    NOT NULL,
    loan_amount          DECIMAL(15,2)  NOT NULL,
    interest_rate        DECIMAL(6,4)   NOT NULL,     -- e.g. 0.0675 = 6.75%
    loan_term_months     INT            NULL,
    credit_score         INT            NOT NULL,
    annual_income        DECIMAL(12,2)  NOT NULL,
    dti_ratio            DECIMAL(5,3)   NOT NULL,     -- e.g. 0.35 = 35%
    borrower_segment     VARCHAR(20)    NOT NULL,     -- Prime | Near-Prime | Subprime | Deep Subprime
    delinquency_status   VARCHAR(20)    NOT NULL,     -- Current | 30-59 DPD | 60-89 DPD | 90+ DPD | Default | Charged-Off
    days_past_due        INT            NOT NULL  DEFAULT 0,
    loss_given_default   DECIMAL(15,2)  NOT NULL  DEFAULT 0,
    prob_of_default      DECIMAL(6,4)   NULL,
    origination_year     INT            NULL,
    origination_quarter  VARCHAR(7)     NULL,         -- e.g. 2022Q1

    CONSTRAINT pk_loan_portfolio  PRIMARY KEY (loan_id),
    CONSTRAINT chk_credit_score   CHECK (credit_score  BETWEEN 300 AND 850),
    CONSTRAINT chk_dti            CHECK (dti_ratio      BETWEEN 0   AND 1),
    CONSTRAINT chk_interest_rate  CHECK (interest_rate  BETWEEN 0   AND 1),
    CONSTRAINT chk_loan_amount    CHECK (loan_amount    > 0)
);
GO


-- TABLE 2: delinquency_history
-- Monthly portfolio snapshot — drives the trend line charts
CREATE TABLE delinquency_history (
    snapshot_month       VARCHAR(7)     NOT NULL,    -- YYYY-MM, e.g. 2023-06
    total_loans          INT            NOT NULL,
    delinquent_loans     INT            NOT NULL,
    avg_credit_score     DECIMAL(6,2)   NULL,
    total_balance        DECIMAL(18,2)  NULL,
    delinquency_rate     DECIMAL(6,4)   NULL,        -- e.g. 0.1704 = 17.04%

    CONSTRAINT pk_delinquency_history PRIMARY KEY (snapshot_month)
);
GO


-- TABLE 3: loan_risk_scores
-- ML model output — one PD score row per loan
CREATE TABLE loan_risk_scores (
    loan_id              VARCHAR(10)    NOT NULL,
    model_pd             DECIMAL(6,4)   NULL,        -- predicted probability of default, 0-1
    risk_band            VARCHAR(10)    NULL,        -- Low | Medium | High | Critical
    score_date           DATE           NULL,
    model_version        VARCHAR(10)    NULL,        -- e.g. GBM_v1.0

    CONSTRAINT pk_loan_risk_scores PRIMARY KEY (loan_id),
    CONSTRAINT fk_risk_loan        FOREIGN KEY (loan_id)
                                   REFERENCES loan_portfolio(loan_id)
);
GO


-- ── Step 4: Create indexes ────────────────────────────────────
CREATE INDEX idx_loan_state         ON loan_portfolio(state);
CREATE INDEX idx_loan_type          ON loan_portfolio(loan_type);
CREATE INDEX idx_delinquency_status ON loan_portfolio(delinquency_status);
CREATE INDEX idx_borrower_segment   ON loan_portfolio(borrower_segment);
CREATE INDEX idx_origination_year   ON loan_portfolio(origination_year);
CREATE INDEX idx_credit_score       ON loan_portfolio(credit_score);
CREATE INDEX idx_risk_band          ON loan_risk_scores(risk_band);
GO


-- ── Step 5: Verify ────────────────────────────────────────────
SELECT TABLE_NAME, TABLE_TYPE
FROM   INFORMATION_SCHEMA.TABLES
WHERE  TABLE_CATALOG = 'loan_risk_db'
  AND  TABLE_TYPE    = 'BASE TABLE'
ORDER  BY TABLE_NAME;
GO
