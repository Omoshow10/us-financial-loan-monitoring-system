# Setup Guide
## US Financial Loan Monitoring System

Step-by-step instructions to get the full project running locally.

**Database platform: Microsoft SQL Server 2019+**

---

## Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| SQL Server | 2019+ (any edition, including free Express) | https://www.microsoft.com/en-us/sql-server/sql-server-downloads |
| SQL Server Management Studio (SSMS) | 19+ | https://aka.ms/ssmsfullsetup |
| Python | 3.9+ | https://www.python.org/downloads/ |
| Power BI Desktop | Latest (free) | https://powerbi.microsoft.com/desktop |
| Git | Any | https://git-scm.com/ |

> **SQL Server Express** is free with no time limit. It supports databases up to 10 GB, which is more than enough for this project. Download it from the link above and choose the Express edition.

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/us-financial-loan-monitoring.git
cd us-financial-loan-monitoring
```

---

## Step 2 — Python Environment Setup

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux

# Install all dependencies
pip install -r python/requirements.txt
```

---

## Step 3 — Generate the Dataset and Train the Model

Run these two Python scripts in order. The first generates the loan data; the second trains the Probability of Default model and adds PD scores to the dataset.

```bash
python python/01_data_generation.py
python python/03_default_prediction.py
```

Expected output from the first script:
```
loan_portfolio.csv → 5,000 rows
Delinquency rate: 17.04%
Charge-off rate:  1.54%
Total portfolio:  $0.71B
Avg credit score: 700
```

Expected output from the second script:
```
Logistic Regression  AUC=0.8195  ← Best model selected
Random Forest        AUC=0.8035
Gradient Boosting    AUC=0.7655

Saved: loan_portfolio_scored.csv (5,000 rows)
```

After both scripts complete, these two files will exist in `data/processed/`:
- `loan_portfolio.csv` — 5,000 loans with risk attributes
- `loan_portfolio_scored.csv` — same loans plus `model_pd` and `risk_band` columns

---

## Step 4 — Set Up SQL Server

### 4.1 — Install SQL Server and SSMS

If you do not already have SQL Server installed:
1. Go to https://www.microsoft.com/en-us/sql-server/sql-server-downloads
2. Click **Download now** under the **Express** (free) edition
3. Run the installer and choose **Basic** installation
4. Note the server name shown at the end — usually `localhost\SQLEXPRESS`
5. Download and install **SSMS** from https://aka.ms/ssmsfullsetup
6. Open SSMS and connect using the server name from step 4

### 4.2 — Run the Schema Script

In SSMS:
1. File → Open → `sql/01_create_schema.sql`
2. Click **Execute** (or press F5)

This creates the `loan_risk_db` database and the three tables: `loan_portfolio`, `delinquency_history`, and `loan_risk_scores`.

Expected output in the Messages panel:
```
(0 rows affected)   ← CREATE DATABASE
(0 rows affected)   ← CREATE TABLE ×3
(0 rows affected)   ← CREATE INDEX ×7
TABLE_NAME
-----------------------
delinquency_history
loan_portfolio
loan_risk_scores
```

### 4.3 — Update the File Paths in the Ingestion Script

Open `sql/03_data_ingestion.sql` in any text editor. Find the two `BULK INSERT` commands and update the file paths to match the actual location of your project folder on your machine.

**Replace:**
```
C:\Projects\us-financial-loan-monitoring\data\processed\loan_portfolio.csv
```
**With your actual path, for example:**
```
C:\Users\YourName\Documents\us-financial-loan-monitoring\data\processed\loan_portfolio.csv
```

Do this for both `BULK INSERT` statements (one for `loan_portfolio`, one for `loan_risk_scores`).

> **Important:** Use backslashes `\` not forward slashes `/` in the file paths.

### 4.4 — Run the Data Ingestion Script

In SSMS:
1. File → Open → `sql/03_data_ingestion.sql`
2. Click **Execute**

Expected output:
```
(5000 rows affected)   ← loan_portfolio loaded
(5000 rows affected)   ← loan_risk_scores loaded
(5000 rows affected)   ← score_date stamped
(24 rows affected)     ← delinquency_history populated

table_name           | row_count
---------------------|----------
loan_portfolio       | 5000
loan_risk_scores     | 5000
delinquency_history  | 24
```

### 4.5 — Run the Dashboard and Segmentation Queries

In SSMS, open and execute each script to verify the queries work:

```
sql/02_dashboard_queries.sql
sql/04_risk_segmentation.sql
```

Each script contains multiple `GO`-separated query blocks. You can run the entire script with F5, or highlight individual blocks and run them with F5.

---

## Step 5 — Connect Power BI to SQL Server

### Option A — Connect directly to SQL Server (recommended for live refresh)

1. Open **Power BI Desktop**
2. **Home → Get Data → SQL Server**
3. Enter your server name (e.g., `localhost\SQLEXPRESS` or `localhost`)
4. Enter database name: `loan_risk_db`
5. Click **OK** → select `loan_portfolio` and `loan_risk_scores` tables → **Load**

### Option B — Load from CSV (simpler, no SQL Server connection needed)

1. Open **Power BI Desktop**
2. **Home → Get Data → Text/CSV**
3. Select `data/processed/loan_portfolio_scored.csv`
4. Click **Load**

### After loading data

1. Create the `DateTable` using the DAX formula in `powerbi/DAX_measures.md`
2. Create all measures from `powerbi/DAX_measures.md`
3. Build the four report pages as described in `powerbi/data_model.md`

---

## Troubleshooting

### Cannot connect to SQL Server in SSMS

Confirm the SQL Server service is running:
- Press Windows key → type `services.msc` → press Enter
- Find **SQL Server (MSSQLSERVER)** or **SQL Server (SQLEXPRESS)**
- Right-click → **Start** if it is not running

Try these server name formats if `localhost` does not work:
```
localhost\SQLEXPRESS     ← Express edition
localhost                ← Developer or Standard edition
.\SQLEXPRESS             ← Alternative for Express
(local)                  ← Alternative for default instance
```

### BULK INSERT fails — file could not be opened

SQL Server needs read permission on the folder containing your CSV files:
1. In File Explorer, right-click the `data\processed` folder → **Properties**
2. Click **Security** tab → **Edit** → **Add**
3. Type the SQL Server service account name (found in services.msc under "Log On As")
4. Give it **Read** permission → **OK**

Alternatively, grant the permission in SSMS (run as admin):
```sql
GRANT ADMINISTER BULK OPERATIONS TO [your_login];
```

### BULK INSERT fails — cannot find file

The file path in the script uses a placeholder. You must update it to your actual path before running. See Step 4.3 above.

### Python: ModuleNotFoundError

```bash
pip install -r python/requirements.txt --upgrade
```

### Power BI: Cannot connect to data source

- For SQL Server connection: verify the server name is correct and the SQL Server service is running
- For CSV connection: use the full absolute path, not a relative path

---

## Project File Map

```
us-financial-loan-monitoring/
│
├── sql/
│   ├── 01_create_schema.sql       ← Run first: database, tables, indexes
│   ├── 02_dashboard_queries.sql   ← KPI queries for all four dashboard pages
│   ├── 03_data_ingestion.sql      ← Loads CSV data via BULK INSERT
│   └── 04_risk_segmentation.sql   ← Segment matrix, watchlist, vintage analysis
│
├── python/
│   ├── 01_data_generation.py      ← Run first — generates loan_portfolio.csv
│   ├── 02_eda_analysis.py         ← Portfolio overview charts (optional)
│   ├── 03_default_prediction.py   ← Run second — trains PD model, adds scores
│   └── requirements.txt
│
├── powerbi/
│   ├── POWERBI_SETUP.md           ← Dashboard build guide
│   ├── DAX_measures.md            ← All DAX formulas
│   └── LoanRisk_theme.json        ← Custom dark theme
│
├── data/
│   └── processed/
│       ├── loan_portfolio.csv         ← Generated by Step 3
│       └── loan_portfolio_scored.csv  ← Generated by Step 3 (Power BI input)
│
├── outputs/
│   ├── eda_charts.png             ← 6-panel risk analysis chart
│   ├── portfolio_overview.png     ← 9-panel portfolio overview
│   └── model_performance.png      ← ROC curves + confusion matrix
│
└── docs/
    ├── setup_guide.md             ← This file
    └── methodology.md             ← Risk metric definitions
```
