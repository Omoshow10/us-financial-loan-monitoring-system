-- ============================================================
-- US Financial Loan Monitoring System
-- Script 01: Database Schema Creation
-- Compatible with: SQL Server / PostgreSQL / SQLite
-- ============================================================

-- Drop existing tables (order respects FK dependencies)
DROP TABLE IF EXISTS loan_risk_scores;
DROP TABLE IF EXISTS delinquency_history;
DROP TABLE IF EXISTS loan_portfolio;

-- ──────────────────────────────────────────────────────────────
-- Core loan portfolio table
-- ──────────────────────────────────────────────────────────────
CREATE TABLE loan_portfolio (
    loan_id              VARCHAR(10)    PRIMARY KEY,
    origination_date     DATE           NOT NULL,
    state                CHAR(2)        NOT NULL,
    loan_type            VARCHAR(20)    NOT NULL,
    loan_amount          DECIMAL(15,2)  NOT NULL,
    interest_rate        DECIMAL(6,4)   NOT NULL,       -- e.g. 0.0675 = 6.75%
    loan_term_months     INT,
    credit_score         INT            NOT NULL,
    annual_income        DECIMAL(12,2)  NOT NULL,
    dti_ratio            DECIMAL(5,3)   NOT NULL,       -- debt-to-income ratio
    borrower_segment     VARCHAR(20)    NOT NULL,       -- Prime | Near-Prime | Subprime | Deep Subprime
    delinquency_status   VARCHAR(20)    NOT NULL,       -- Current | 30-59 DPD | 60-89 DPD | 90+ DPD | Default | Charged-Off
    days_past_due        INT            DEFAULT 0,
    loss_given_default   DECIMAL(15,2)  DEFAULT 0,
    prob_of_default      DECIMAL(6,4),
    origination_year     INT,
    origination_quarter  VARCHAR(7),

    -- Constraints
    CONSTRAINT chk_credit_score   CHECK (credit_score BETWEEN 300 AND 850),
    CONSTRAINT chk_dti            CHECK (dti_ratio BETWEEN 0 AND 1),
    CONSTRAINT chk_interest_rate  CHECK (interest_rate BETWEEN 0 AND 1),
    CONSTRAINT chk_loan_amount    CHECK (loan_amount > 0)
);

-- ──────────────────────────────────────────────────────────────
-- Monthly delinquency snapshot (for trend analysis)
-- ──────────────────────────────────────────────────────────────
CREATE TABLE delinquency_history (
    snapshot_month       VARCHAR(7)     NOT NULL,   -- YYYY-MM format
    total_loans          INT            NOT NULL,
    delinquent_loans     INT            NOT NULL,
    avg_credit_score     DECIMAL(6,2),
    total_balance        DECIMAL(18,2),
    delinquency_rate     DECIMAL(6,4),
    PRIMARY KEY (snapshot_month)
);

-- ──────────────────────────────────────────────────────────────
-- Model-scored risk table (populated by Python model)
-- ──────────────────────────────────────────────────────────────
CREATE TABLE loan_risk_scores (
    loan_id              VARCHAR(10)    PRIMARY KEY,
    model_pd             DECIMAL(6,4),   -- predicted probability of default
    risk_band            VARCHAR(10),    -- Low | Medium | High | Critical
    score_date           DATE,
    model_version        VARCHAR(10),
    FOREIGN KEY (loan_id) REFERENCES loan_portfolio(loan_id)
);

-- ──────────────────────────────────────────────────────────────
-- Indexes for dashboard query performance
-- ──────────────────────────────────────────────────────────────
CREATE INDEX idx_loan_state          ON loan_portfolio(state);
CREATE INDEX idx_loan_type           ON loan_portfolio(loan_type);
CREATE INDEX idx_delinquency_status  ON loan_portfolio(delinquency_status);
CREATE INDEX idx_borrower_segment    ON loan_portfolio(borrower_segment);
CREATE INDEX idx_origination_year    ON loan_portfolio(origination_year);
CREATE INDEX idx_credit_score        ON loan_portfolio(credit_score);
