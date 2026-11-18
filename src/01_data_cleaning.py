# %% [markdown]
# # 01 – Data Cleaning & Preprocessing
# Credit Risk Analysis & Loan Repayment Behaviour. Input: `data/Loan_data_combined.csv`, output: `data/loan_data_cleaned.csv`.

# %%
import numpy as np, pandas as pd
RAW, OUT = "data/Loan_data_combined.csv", "data/loan_data_cleaned.csv"
df = pd.read_csv(RAW)
print("Raw shape:", df.shape)

# %% [markdown]
# ## 1. Quality audit

# %%
miss = (df.isna().mean() * 100).round(1).sort_values(ascending=False)
print(miss[miss > 0])
print("\nExact duplicate rows:", df.duplicated().sum())
print("Repeated SK_ID_CURR (valid: one customer, many past applications):", df.SK_ID_CURR.duplicated().sum())
print("\nDAYS_* sentinel 365243 counts:\n", (df.filter(like="DAYS_") == 365243).sum())

# %% [markdown]
# ## 2. Remove duplicates, standardise text

# %%
df = df.drop_duplicates().reset_index(drop=True)
cat_cols = df.select_dtypes(exclude="number").columns
df[cat_cols] = df[cat_cols].apply(lambda s: s.str.strip())
df["WEEKDAY_APPR_PROCESS_START"] = df["WEEKDAY_APPR_PROCESS_START"].str.title()
# XNA / XAP are the dataset's "not available / not applicable" codes
df[cat_cols] = df[cat_cols].replace({"XNA": "Unknown", "XAP": "Not Applicable"})

# %% [markdown]
# ## 3. Sentinel values
# `365243` days (~1000 years) is a placeholder for "event never happened"; `SELLERPLACE_AREA = -1` means unknown.

# %%
day_cols = [c for c in df.columns if c.startswith("DAYS_")]
df[day_cols] = df[day_cols].replace(365243, np.nan)
df["SELLERPLACE_AREA"] = df["SELLERPLACE_AREA"].replace(-1, np.nan)

# %% [markdown]
# ## 4. Missing values
# * RATE_INTEREST_* are ~99.7 % empty → dropped.
# * Down payment fields: blank = no down payment → 0.
# * Annuity, goods price, instalment count: median **per contract type** (robust to skew).
# * DAYS_FIRST_*/LAST_*/TERMINATION & insurance flag are blank for loans never drawn (refused / cancelled) → kept as NULL on purpose.
# * NAME_TYPE_SUITE, PRODUCT_COMBINATION → "Unknown".

# %%
df = df.drop(columns=["RATE_INTEREST_PRIMARY", "RATE_INTEREST_PRIVILEGED"])
df[["AMT_DOWN_PAYMENT", "RATE_DOWN_PAYMENT"]] = df[["AMT_DOWN_PAYMENT", "RATE_DOWN_PAYMENT"]].fillna(0)
for c in ["AMT_ANNUITY", "AMT_GOODS_PRICE", "CNT_PAYMENT"]:
    df[c] = df[c].fillna(df.groupby("NAME_CONTRACT_TYPE")[c].transform("median")).fillna(df[c].median())
df[["NAME_TYPE_SUITE", "PRODUCT_COMBINATION"]] = df[["NAME_TYPE_SUITE", "PRODUCT_COMBINATION"]].fillna("Unknown")

# %% [markdown]
# ## 5. Outliers (IQR rule)
# Large loans are genuine business cases, so values are **flagged, not removed** – this keeps SQL totals accurate.

# %%
def iqr_flag(s):
    q1, q3 = s.quantile([.25, .75]); i = q3 - q1
    return ((s < q1 - 1.5 * i) | (s > q3 + 1.5 * i)).astype(int)

for c in ["AMT_ANNUITY", "AMT_APPLICATION", "AMT_CREDIT", "AMT_GOODS_PRICE"]:
    df[f"OUTLIER_{c}"] = iqr_flag(df[c])
    print(c, "outliers:", df[f"OUTLIER_{c}"].sum())

# %% [markdown]
# ## 6. Feature engineering

# %%
df["YEARS_SINCE_DECISION"] = (-df["DAYS_DECISION"] / 365).round(1)
df["DECISION_YEAR_BUCKET"] = pd.cut(df["YEARS_SINCE_DECISION"], [-1, 1, 2, 4, 6, 10],
                                    labels=["<1y", "1-2y", "2-4y", "4-6y", "6y+"])
df["CREDIT_BAND"] = pd.cut(df["AMT_CREDIT"], [-1, 50_000, 150_000, 500_000, np.inf],
                           labels=["Low (<50K)", "Medium (50-150K)", "High (150-500K)", "Very High (>500K)"])
df["IS_APPROVED"] = (df["NAME_CONTRACT_STATUS"] == "Approved").astype(int)
df["IS_REFUSED"] = (df["NAME_CONTRACT_STATUS"] == "Refused").astype(int)
df["CREDIT_TO_APPLICATION_RATIO"] = (df["AMT_CREDIT"] / df["AMT_APPLICATION"].replace(0, np.nan)).round(3)
for c in ["DECISION_YEAR_BUCKET", "CREDIT_BAND"]:
    df[c] = df[c].astype(str).replace("nan", "Unknown")

# %% [markdown]
# ## 7. Save

# %%
df.to_csv(OUT, index=False)
print("Clean shape:", df.shape)
print(df.isna().sum()[df.isna().sum() > 0])
