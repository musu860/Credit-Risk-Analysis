"""Load the cleaned CSV into PostgreSQL (or MySQL) via SQLAlchemy.
Usage:  python src/02_load_to_db.py
Env:    DB_URL
  PostgreSQL: postgresql+psycopg2://postgres:PASSWORD@localhost:5432/credit_risk_db
  MySQL:      mysql+pymysql://root:PASSWORD@localhost:3306/credit_risk_db
Run the matching schema file first (sql/schema_postgres.sql or sql/schema.sql)."""
import os, numpy as np, pandas as pd
from sqlalchemy import create_engine

DB_URL = os.getenv("DB_URL", "postgresql+psycopg2://postgres:password@localhost:5432/credit_risk_db")
df = pd.read_csv("data/loan_data_cleaned.csv")
df.columns = df.columns.str.lower()          # PostgreSQL folds unquoted names to lowercase
df = df.astype(object).where(df.notna(), None)
engine = create_engine(DB_URL)
df.to_sql("loan_data", engine, if_exists="append", index=False, chunksize=2000, method="multi")
print(f"Loaded {len(df):,} rows into loan_data")
