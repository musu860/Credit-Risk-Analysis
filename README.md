# Credit Risk Analysis & Loan Repayment Behaviour (EDA + MySQL + Streamlit)

## Folder structure
```
data/        Loan_data_combined.csv (raw), loan_data_cleaned.csv (output)
src/         01_data_cleaning.py, 02_load_to_db.py, 03_eda.py, build_notebooks.py
notebooks/   01_data_cleaning.ipynb, 03_eda.ipynb
sql/         schema_postgres.sql, schema.sql (MySQL), queries.sql (20 queries)
charts/      EDA charts (PNG)
app.py       Streamlit dashboard (reads from MySQL)
```

## How to run (PostgreSQL)
```bash
pip install -r requirements.txt
python src/01_data_cleaning.py                       # -> data/loan_data_cleaned.csv
# in pgAdmin/psql: CREATE DATABASE credit_risk_db;  then run sql/schema_postgres.sql on it
export DB_URL="postgresql+psycopg2://postgres:YOURPASSWORD@localhost:5432/credit_risk_db"
python src/02_load_to_db.py
streamlit run app.py
```
(Windows PowerShell: `$env:DB_URL="postgresql+psycopg2://..."`.)
For MySQL use `sql/schema.sql` and `mysql+pymysql://root:PASSWORD@localhost:3306/credit_risk_db`.

## Data notes
* 50,000 rows × 36 columns -> 49,896 after removing 104 exact duplicates. 44 columns after cleaning/feature engineering.
* This is **previous-application** data (Home Credit style). It has **no default/TARGET column and no age, income, education or occupation**, so
  "repayment difficulty" is measured by **refusal rate**, and dashboard filters use contract type, client type, credit band, portfolio and decision recency instead.
* `365243` in DAYS_* columns = placeholder for "never happened" -> NaN. `XNA`/`XAP` -> `Unknown` / `Not Applicable`.
* RATE_INTEREST_* (99.7 % empty) dropped. Outliers are flagged (IQR), not deleted, so SQL totals stay accurate.
* The dataset has one table, so the "join-based" questions are implemented as filters / aggregations on `loan_data`.

## Key findings
| Finding | Evidence |
|---|---|
| Overall: 63.9 % approved, 17.3 % refused, 17.0 % cancelled | status split |
| Consumer loans are safest: 10.5 % refusal, 85.7 % approval | Cash 22.8 %, Revolving 25.8 % refusal |
| Refusal climbs with loan size | <50K: 10.3 % -> >500K: **39.9 %** |
| Repeat customers refused more than new | Repeater 21.5 %, New 4.3 % |
| Cards & Cash portfolios riskiest | 32.3 % and 30.6 % refusal vs POS 9.4 % |
| Corporate-sales channel & AP+ (cash loan) channel riskiest | 57.2 % and 39.1 % (corporate channel only 276 apps) |
| Top rejection reason | `HC` = 5,076 of ~8,650 refusals (~59 %), then LIMIT, SCO |
| Recent applications refused more | <1 year: 20.1 % vs 2-6 years: ~13.5 % |
| 18.3 % of customers have at least one refusal | 44,471 customers, 4,774 with >1 application |

All segment differences tested with chi-square / Mann-Whitney (p < 0.001). Association, not causation.

## Business recommendations
1. Tighter underwriting / pricing tiers for credit above 500K and for Cash/Cards portfolios.
2. Review repeater-customer rules: high refusal here suggests re-lending to customers whose profile changed.
3. Audit the corporate-sales and AP+ channels for application-quality problems.
4. Investigate the `HC` reject code and whether its criteria are consistent.
5. Collect a real repayment/default flag and income/age fields to move from refusal proxy to true default analysis.

## Caveat
`app.py` needs a running PostgreSQL/MySQL instance. The SQL was validated on the cleaned data using SQLite (no Postgres/MySQL server was available here); syntax is standard, but run it once on your server to confirm.
