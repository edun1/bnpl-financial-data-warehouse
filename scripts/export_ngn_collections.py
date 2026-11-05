from pathlib import Path
import duckdb

root = Path(__file__).resolve().parents[1]
output = root / "exports" / "ngn_collections.csv"
output.parent.mkdir(parents=True, exist_ok=True)

with duckdb.connect(
    str(root / "data" / "bnpl_ngn.duckdb"),
    read_only=True,
) as conn:
    df = conn.execute("""
        SELECT *
        FROM analytics_gold.gold_ngn_collections
        ORDER BY
            as_of_date,
            currency,
            CASE ageing_bucket
                WHEN 'Paid' THEN 0
                WHEN 'Not yet due' THEN 1
                WHEN 'Due today' THEN 2
                WHEN '1-30 days' THEN 3
                WHEN '31-60 days' THEN 4
                WHEN '61-90 days' THEN 5
                WHEN '91+ days' THEN 6
                ELSE 7
            END
    """).fetchdf()

df.to_csv(output, index=False)

print(df.to_string(index=False))
print(f"\nExported {len(df)} rows")
print(f"Saved to: {output}")