"""
generate_data.py
Generates a realistic synthetic US loan portfolio dataset.
Outputs to data/processed/
"""
import pandas as pd
import numpy as np
import os

np.random.seed(42)
N = 5000

states = ["CA","TX","FL","NY","IL","PA","OH","GA","NC","MI","NJ","VA","WA","AZ","MA","TN","IN","MO","MD","CO","WI","MN","SC","AL","LA","KY","OR","OK","CT","UT","IA","NV","AR","MS","KS","NM","NE","ID","WV","HI","NH","ME","MT","RI","DE","SD","ND","AK","VT","WY"]
state_weights = np.array([0.12,0.09,0.08,0.08,0.05,0.04,0.04,0.03,0.03,0.03,0.03,0.03,0.03,0.02,0.02,0.02,0.02,0.02,0.02,0.02,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.005,0.005,0.005,0.005,0.005,0.005,0.005,0.005,0.005,0.003,0.003,0.003,0.002,0.002,0.001,0.001])
state_weights /= state_weights.sum()

loan_types = ["Mortgage","Auto","Personal","Student","Small Business","Credit Card"]
loan_type_weights = [0.40,0.22,0.15,0.10,0.08,0.05]

start = pd.Timestamp("2019-01-01")
end   = pd.Timestamp("2024-12-31")
orig_dates = pd.to_datetime(np.random.randint(start.value, end.value, N), unit="ns").normalize()

state_col     = np.random.choice(states, size=N, p=state_weights)
loan_type_col = np.random.choice(loan_types, size=N, p=loan_type_weights)

bands = np.random.choice(["Poor","Fair","Good","VeryGood","Exceptional"], size=N, p=[0.12,0.18,0.25,0.27,0.18])
credit_scores = np.where(bands=="Poor", np.random.randint(300,580,N),
               np.where(bands=="Fair", np.random.randint(580,670,N),
               np.where(bands=="Good", np.random.randint(670,740,N),
               np.where(bands=="VeryGood", np.random.randint(740,800,N),
                         np.random.randint(800,851,N)))))

income = np.random.lognormal(mean=11.0, sigma=0.5, size=N).astype(int)
dti = np.clip(np.random.beta(2,5,N)*0.8+0.05, 0.05, 0.75).round(3)
interest_rate = np.clip(0.02 + (850-credit_scores)/850*0.18 + np.random.normal(0,0.005,N), 0.01, 0.30).round(4)

loan_amounts = np.where(loan_type_col=="Mortgage", np.random.lognormal(12.5,0.5,N).astype(int),
               np.where(loan_type_col=="Auto", np.random.lognormal(10.2,0.4,N).astype(int),
               np.where(loan_type_col=="Personal", np.random.lognormal(9.5,0.5,N).astype(int),
               np.where(loan_type_col=="Student", np.random.lognormal(10.3,0.4,N).astype(int),
               np.where(loan_type_col=="Small Business", np.random.lognormal(11.5,0.6,N).astype(int),
                         np.random.lognormal(8.8,0.5,N).astype(int))))))

term_map = {"Mortgage":360,"Auto":60,"Personal":48,"Student":120,"Small Business":84,"Credit Card":0}
loan_term = np.array([term_map[lt] for lt in loan_type_col])

# Target ~18% delinquency rate (realistic for a stressed portfolio)
# Assign delinquency based on credit score band
prob_delinquent = np.where(bands=="Poor", np.random.uniform(0.45,0.65,N),
                  np.where(bands=="Fair", np.random.uniform(0.25,0.40,N),
                  np.where(bands=="Good", np.random.uniform(0.10,0.20,N),
                  np.where(bands=="VeryGood", np.random.uniform(0.03,0.08,N),
                            np.random.uniform(0.01,0.04,N)))))

is_delinquent = np.random.rand(N) < prob_delinquent
raw_status = np.random.choice(["30-59 DPD","60-89 DPD","90+ DPD","Default","Charged-Off"], size=N, p=[0.35,0.25,0.20,0.12,0.08])
delinquency_status = np.where(is_delinquent, raw_status, "Current")

dpd_map = {"Current":0,"30-59 DPD":45,"60-89 DPD":75,"90+ DPD":110,"Default":180,"Charged-Off":365}
days_past_due = np.clip(np.array([dpd_map[s] for s in delinquency_status]) + np.random.randint(-5,5,N), 0, 999)

is_loss = np.isin(delinquency_status, ["Default","Charged-Off"])
recovery_rate = np.where(is_loss, np.random.beta(2,5,N), 1.0)
lgd = np.where(is_loss, loan_amounts*(1-recovery_rate), 0).astype(int)
prob_default = np.clip(prob_delinquent*0.45, 0, 1).round(4)

def segment(score, d, inc):
    if score>=740 and d<0.36 and inc>70000: return "Prime"
    elif score>=670 and d<0.43: return "Near-Prime"
    elif score>=580: return "Subprime"
    else: return "Deep Subprime"
borrower_segment = np.array([segment(cs,d,i) for cs,d,i in zip(credit_scores,dti,income)])

df = pd.DataFrame({
    "loan_id": [f"LN{str(i).zfill(6)}" for i in range(1,N+1)],
    "origination_date": orig_dates,
    "state": state_col,
    "loan_type": loan_type_col,
    "loan_amount": loan_amounts,
    "interest_rate": interest_rate,
    "loan_term_months": loan_term,
    "credit_score": credit_scores,
    "annual_income": income,
    "dti_ratio": dti,
    "borrower_segment": borrower_segment,
    "delinquency_status": delinquency_status,
    "days_past_due": days_past_due,
    "loss_given_default": lgd,
    "prob_of_default": prob_default,
    "origination_year": orig_dates.year,
    "origination_quarter": orig_dates.to_period("Q").astype(str),
})

month_col = df["origination_date"].dt.to_period("M")
trend = df.copy()
trend["month"] = month_col
trend = trend.groupby("month").agg(
    total_loans=("loan_id","count"),
    delinquent_loans=("delinquency_status", lambda x: (x!="Current").sum()),
    avg_credit_score=("credit_score","mean"),
    total_balance=("loan_amount","sum"),
).reset_index()
trend["delinquency_rate"] = (trend["delinquent_loans"]/trend["total_loans"]).round(4)
trend["month"] = trend["month"].astype(str)

geo = df.groupby("state").agg(
    total_loans=("loan_id","count"),
    total_balance=("loan_amount","sum"),
    avg_credit_score=("credit_score","mean"),
    delinquent_loans=("delinquency_status", lambda x: (x!="Current").sum()),
    charged_off_loans=("delinquency_status", lambda x: (x=="Charged-Off").sum()),
    total_lgd=("loss_given_default","sum"),
).reset_index()
geo["delinquency_rate"] = (geo["delinquent_loans"]/geo["total_loans"]).round(4)
geo["charge_off_rate"]  = (geo["charged_off_loans"]/geo["total_loans"]).round(4)
geo["avg_loan_balance"] = (geo["total_balance"]/geo["total_loans"]).astype(int)
geo["risk_tier"] = pd.cut(geo["delinquency_rate"], bins=[0,0.08,0.15,0.25,1.0], labels=["Low","Moderate","High","Critical"])

seg = df.groupby("borrower_segment").agg(
    total_loans=("loan_id","count"),
    avg_credit_score=("credit_score","mean"),
    avg_dti=("dti_ratio","mean"),
    avg_income=("annual_income","mean"),
    delinquent_loans=("delinquency_status", lambda x: (x!="Current").sum()),
    avg_prob_default=("prob_of_default","mean"),
    total_lgd=("loss_given_default","sum"),
).reset_index()
seg["delinquency_rate"] = (seg["delinquent_loans"]/seg["total_loans"]).round(4)

base = "/home/claude/us-financial-loan-monitoring/data/processed"
df.to_csv(f"{base}/loan_portfolio.csv", index=False)
trend.to_csv(f"{base}/delinquency_trends.csv", index=False)
geo.to_csv(f"{base}/geographic_risk.csv", index=False)
seg.to_csv(f"{base}/borrower_segments.csv", index=False)

print(f"loan_portfolio.csv → {len(df):,} rows")
print(f"Delinquency rate: {(df['delinquency_status']!='Current').mean():.2%}")
print(f"Charge-off rate:  {(df['delinquency_status']=='Charged-Off').mean():.2%}")
print(f"Total portfolio:  ${df['loan_amount'].sum()/1e9:.2f}B")
print(f"Avg credit score: {df['credit_score'].mean():.0f}")
