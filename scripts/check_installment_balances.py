from pathlib import Path
import duckdb

database = Path(__file__).resolve().parents[1] / "data" / "bnpl_ngn.duckdb"

with duckdb.connect(str(database), read_only=True) as conn:
    totals = conn.execute("""
        SELECT
            COUNT(*) AS installments,
            SUM(amount) AS total_amount,
            SUM(paid_amount) AS paid,
            SUM(outstanding_amount) AS outstanding,
            SUM(overdue_amount) AS overdue,
            SUM(due_today_amount) AS due_today,
            SUM(future_due_amount) AS future_due
        FROM analytics_silver.fact_installments
    """).fetchone()

    labels = [
        "Installments", "Total amount", "Paid",
        "Outstanding", "Overdue", "Due today", "Future due"
    ]

    for label, value in zip(labels, totals):
        print(f"{label}: {value:,.2f}" if label != "Installments"
              else f"{label}: {value:,}")

    invalid = conn.execute("""
        SELECT COUNT(*)
        FROM analytics_silver.fact_installments
        WHERE amount IS NULL
           OR currency IS DISTINCT FROM 'NGN'
           OR as_of_date IS NULL
           OR customer_id IS NULL
           OR due_date IS NULL
           OR amount <> paid_amount + outstanding_amount
           OR outstanding_amount <>
                overdue_amount + due_today_amount + future_due_amount
    """).fetchone()[0]

    plan_total = conn.execute("""
        SELECT SUM(total_amount)
        FROM analytics_staging.stg_payment_plans
    """).fetchone()[0]

    assert totals[0] == 2000, "Expected 2,000 installments"
    assert invalid == 0, f"Found {invalid} invalid installment balances"
    assert totals[1] == plan_total, "Installments do not match plan totals"

    print("Installment and plan reconciliation: PASS")