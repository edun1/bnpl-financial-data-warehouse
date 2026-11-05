"""Generate synthetic NGN BNPL data using a fixed reporting date."""

import csv
from datetime import date, timedelta
from pathlib import Path
import random


AS_OF = date(2026, 10, 31)
OUTPUT = Path(__file__).resolve().parents[1] / "data/raw_ngn"


def money(kobo):
    return f"{kobo // 100}.{kobo % 100:02d}"


def write_csv(name, records):
    with (OUTPUT / f"{name}.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main():
    rng = random.Random(42)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    customers = [
        {
            "customer_id": f"CUST{i:04d}",
            "first_name": "Synthetic",
            "last_name": f"Customer{i}",
            "email": f"customer{i}@example.com",
            "phone_number": "",
            "country": "Nigeria",
            "city": rng.choice(["Lagos", "Warri", "Abuja", "Kano"]),
            "registration_date": "2025-01-01",
            "last_login_date": AS_OF.isoformat(),
            "status": "active",
        }
        for i in range(1, 101)
    ]

    merchants = [
        {
            "merchant_id": f"MERCH{i:03d}",
            "merchant_name": f"Demo Merchant {i}",
            "category": rng.choice(["Fashion", "Electronics", "Home"]),
            "country": "Nigeria",
            "integration_type": "direct",
            "onboarding_date": "2025-01-01",
            "status": "active",
        }
        for i in range(1, 11)
    ]

    transactions, plans, installments, events = [], [], [], []

    for i in range(1, 501):
        customer_id = rng.choice(customers)["customer_id"]
        merchant_id = rng.choice(merchants)["merchant_id"]
        purchase_date = AS_OF - timedelta(days=rng.randint(0, 180))
        total_kobo = rng.randint(500000, 50000000)
        transaction_id = f"TXN{i:06d}"
        plan_id = f"PLAN{i:06d}"

        # Four payments at 30-day intervals, including one at purchase.
        base, remainder = divmod(total_kobo, 4)
        amounts = [base + (1 if j < remainder else 0) for j in range(4)]
        plan_installments = []

        for j, amount_kobo in enumerate(amounts):
            due = purchase_date + timedelta(days=30 * j)
            paid_date = None

            if due > AS_OF:
                status = "scheduled"
            elif rng.random() < 0.8:
                paid_date = max(
                    purchase_date,
                    min(AS_OF, due + timedelta(days=rng.randint(-3, 20))),
                )
                status = "paid_late" if paid_date > due else "paid"
            else:
                days_past_due = (AS_OF - due).days
                if days_past_due > 90:
                    status = "defaulted"
                elif days_past_due > 0:
                    status = "overdue"
                else:
                    status = "scheduled"

            plan_installments.append({
                "installment_id": f"INST{i:06d}-{j + 1}",
                "plan_id": plan_id,
                "installment_number": j + 1,
                "amount": money(amount_kobo),
                "due_date": due.isoformat(),
                "paid_date": paid_date.isoformat() if paid_date else "",
                "status": status,
                "currency": "NGN",
                "as_of_date": AS_OF.isoformat(),
            })

        statuses = [row["status"] for row in plan_installments]
        if all(status in ("paid", "paid_late") for status in statuses):
            plan_status = "completed"
        elif "defaulted" in statuses:
            plan_status = "defaulted"
        else:
            plan_status = "active"

        transactions.append({
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "merchant_id": merchant_id,
            "transaction_date": purchase_date.isoformat(),
            "amount": money(total_kobo),
            "currency": "NGN",
            "payment_method": "bnpl",
            "status": "completed",
        })

        plans.append({
            "plan_id": plan_id,
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "merchant_id": merchant_id,
            "plan_date": purchase_date.isoformat(),
            "total_amount": money(total_kobo),
            "installment_count": 4,
            "first_installment_amount": money(amounts[0]),
            "status": plan_status,
            "currency": "NGN",
            "as_of_date": AS_OF.isoformat(),
        })

        installments.extend(plan_installments)
        events.append({
            "event_id": f"EVENT{i:06d}",
            "event_timestamp": purchase_date.isoformat() + "T12:00:00",
            "customer_id": customer_id,
            "merchant_id": merchant_id,
            "event_type": "purchase",
            "platform": "web",
            "session_id": f"SESSION{i:06d}",
            "device_type": "desktop",
            "country": "Nigeria",
        })

        assert sum(amounts) == total_kobo

    datasets = {
        "customers": customers,
        "merchants": merchants,
        "transactions": transactions,
        "payment_plans": plans,
        "installments": installments,
        "user_events": events,
    }

    for name, records in datasets.items():
        write_csv(name, records)
        print(f"{name}: {len(records):,}")

    print(f"Reporting date: {AS_OF}")
    print("Installment amount reconciliation: PASS")
    print(f"Saved to: {OUTPUT}")


if __name__ == "__main__":
    main()