"""Load synthetic NGN CSVs into DuckDB in one transaction."""

from contextlib import closing
import csv
from pathlib import Path
import re

import duckdb


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw_ngn"
DATABASE = ROOT / "data/bnpl_ngn.duckdb"

TABLES = [
    "customers",
    "merchants",
    "transactions",
    "payment_plans",
    "installments",
    "user_events",
]

MONEY_COLUMNS = {
    "amount", "total_amount", "first_installment_amount"
}

DATE_COLUMNS = {
    "registration_date", "last_login_date", "onboarding_date",
    "transaction_date", "plan_date", "due_date", "paid_date",
    "as_of_date",
}


def main():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)

    with closing(duckdb.connect(str(DATABASE))) as conn:
        conn.execute("BEGIN TRANSACTION")

        try:
            conn.execute("CREATE SCHEMA IF NOT EXISTS bronze")

            for table in TABLES:
                source = SOURCE / f"{table}.csv"

                with source.open(
                    newline="", encoding="utf-8"
                ) as file:
                    reader = csv.reader(file)
                    columns = next(reader)
                    expected_rows = sum(1 for _ in reader)

                expressions = []

                for column in columns:
                    if not re.fullmatch(r"[a-z_][a-z0-9_]*", column):
                        raise ValueError(f"Unexpected column: {column}")

                    name = f'"{column}"'

                    if column in MONEY_COLUMNS:
                        expression = f"CAST({name} AS DECIMAL(18,2))"
                    elif column in DATE_COLUMNS:
                        expression = f"CAST({name} AS DATE)"
                    elif column == "event_timestamp":
                        expression = f"CAST({name} AS TIMESTAMP)"
                    elif column in {
                        "installment_count", "installment_number"
                    }:
                        expression = f"CAST({name} AS INTEGER)"
                    else:
                        expression = name

                    expressions.append(f"{expression} AS {name}")

                projection = ", ".join(expressions)

                conn.execute(
                    f"""
                    CREATE OR REPLACE TABLE bronze.{table} AS
                    SELECT
                        {projection},
                        current_timestamp AS _etl_extracted_at,
                        ? AS _etl_source
                    FROM read_csv(
                        ?,
                        header=true,
                        all_varchar=true,
                        nullstr=''
                    )
                    """,
                    [f"synthetic_csv.{table}", str(source)],
                )

                actual_rows = conn.execute(
                    f"SELECT COUNT(*) FROM bronze.{table}"
                ).fetchone()[0]

                if actual_rows != expected_rows:
                    raise ValueError(f"Row-count mismatch: {table}")

                print(f"{table}: {actual_rows:,} rows verified")

            mismatches = conn.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT p.plan_id
                    FROM bronze.payment_plans p
                    LEFT JOIN bronze.installments i
                        ON p.plan_id = i.plan_id
                    GROUP BY p.plan_id, p.total_amount,
                             p.installment_count
                    HAVING COUNT(i.installment_id) <> p.installment_count
                       OR COALESCE(SUM(i.amount), 0) <> p.total_amount
                )
            """).fetchone()[0]

            if mismatches:
                raise ValueError(
                    f"{mismatches} payment plans failed reconciliation"
                )

            conn.execute("COMMIT")

        except Exception:
            conn.execute("ROLLBACK")
            raise

    print("Installment count and amount reconciliation: PASS")
    print(f"Database saved: {DATABASE}")


if __name__ == "__main__":
    main()