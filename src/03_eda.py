# %% [markdown]
# # 03 – Exploratory Data Analysis
# Risk proxy: this file has **no default/TARGET flag** (it is previous-application data), so *refusal rate* is used as the credit-risk indicator.

# %%
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt, seaborn as sns
sns.set_theme(style="whitegrid", palette="deep"); os.makedirs("charts", exist_ok=True)
df = pd.read_csv("data/loan_data_cleaned.csv")
def save(name): plt.tight_layout(); plt.savefig(f"charts/{name}.png", dpi=110); plt.show()
print(df.shape); df.describe().T.round(1)

# %% [markdown]
# ## 1. Univariate – status, contract type, client type

# %%
fig, ax = plt.subplots(1, 3, figsize=(16, 4))
for a, c in zip(ax, ["NAME_CONTRACT_STATUS", "NAME_CONTRACT_TYPE", "NAME_CLIENT_TYPE"]):
    vc = df[c].value_counts(); sns.barplot(x=vc.index, y=vc.values, ax=a); a.set_title(c); a.tick_params(axis="x", rotation=20)
save("01_univariate_categories")
print((df.NAME_CONTRACT_STATUS.value_counts(normalize=True) * 100).round(1))

# %% [markdown]
# ## 2. Univariate – amounts (log scale because of heavy right skew)

# %%
fig, ax = plt.subplots(1, 3, figsize=(16, 4))
for a, c in zip(ax, ["AMT_APPLICATION", "AMT_CREDIT", "AMT_ANNUITY"]):
    sns.histplot(np.log1p(df[c]), bins=50, ax=a, kde=True); a.set_title(f"log({c})")
save("02_amount_distributions")
sns.boxplot(data=df, x="NAME_CONTRACT_TYPE", y="AMT_CREDIT"); plt.yscale("log"); save("03_credit_boxplot")

# %% [markdown]
# ## 3. Bivariate – refusal rate by segment (risk indicator)

# %%
def rate(col):
    return (df.groupby(col).agg(apps=("IS_REFUSED", "size"), refusal_pct=("IS_REFUSED", lambda s: 100 * s.mean()),
            approval_pct=("IS_APPROVED", lambda s: 100 * s.mean())).round(1).sort_values("refusal_pct", ascending=False))
for c in ["NAME_CONTRACT_TYPE", "NAME_CLIENT_TYPE", "CREDIT_BAND", "NAME_PORTFOLIO", "CHANNEL_TYPE", "NAME_YIELD_GROUP", "DECISION_YEAR_BUCKET"]:
    print(f"\n--- {c}\n", rate(c))

# %%
fig, ax = plt.subplots(2, 2, figsize=(14, 8))
for a, c in zip(ax.ravel(), ["NAME_CONTRACT_TYPE", "NAME_CLIENT_TYPE", "CREDIT_BAND", "NAME_PORTFOLIO"]):
    r = rate(c).reset_index(); sns.barplot(data=r, x=c, y="refusal_pct", ax=a); a.set_title(f"Refusal % by {c}"); a.tick_params(axis="x", rotation=15)
save("04_refusal_rate_by_segment")

# %% [markdown]
# ## 4. Refusal reasons & loan purpose

# %%
rr = df[df.IS_REFUSED == 1].CODE_REJECT_REASON.value_counts()
print(rr); sns.barplot(x=rr.values, y=rr.index); plt.title("Rejection reasons (refused apps)"); save("05_reject_reasons")

# %% [markdown]
# ## 5. Application timing

# %%
fig, ax = plt.subplots(1, 2, figsize=(15, 4))
order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
sns.countplot(data=df, x="WEEKDAY_APPR_PROCESS_START", order=order, ax=ax[0]); ax[0].tick_params(axis="x", rotation=20)
sns.lineplot(data=df.groupby("HOUR_APPR_PROCESS_START").IS_REFUSED.mean().mul(100).reset_index(), x="HOUR_APPR_PROCESS_START", y="IS_REFUSED", ax=ax[1])
ax[1].set_ylabel("Refusal %"); save("06_timing")

# %% [markdown]
# ## 6. Correlation & statistical test

# %%
num = ["AMT_ANNUITY", "AMT_APPLICATION", "AMT_CREDIT", "AMT_GOODS_PRICE", "AMT_DOWN_PAYMENT", "CNT_PAYMENT",
       "DAYS_DECISION", "HOUR_APPR_PROCESS_START", "IS_REFUSED", "IS_APPROVED"]
plt.figure(figsize=(9, 7)); sns.heatmap(df[num].corr(), annot=True, fmt=".2f", cmap="coolwarm", center=0); save("07_correlation")

from scipy.stats import chi2_contingency, mannwhitneyu
for c in ["NAME_CONTRACT_TYPE", "NAME_CLIENT_TYPE", "NAME_PORTFOLIO"]:
    chi2, p, *_ = chi2_contingency(pd.crosstab(df[c], df.IS_REFUSED)); print(f"Chi-square {c} vs refusal: p = {p:.2e}")
u, p = mannwhitneyu(df[df.IS_REFUSED == 1].AMT_CREDIT, df[df.IS_REFUSED == 0].AMT_CREDIT); print(f"Mann-Whitney credit refused vs not: p = {p:.2e}")

# %% [markdown]
# ## 7. Repeat customers

# %%
cust = df.groupby("SK_ID_CURR").agg(apps=("IS_REFUSED", "size"), refused=("IS_REFUSED", "sum"))
print("Customers:", len(cust), "| with >1 application:", (cust.apps > 1).sum())
print("Customers with at least one refusal: {:.1f}%".format(100 * (cust.refused > 0).mean()))
