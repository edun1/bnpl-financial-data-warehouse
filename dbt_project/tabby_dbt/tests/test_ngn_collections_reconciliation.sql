with silver as (
    select
        as_of_date,
        currency,
        count(*) as installment_count,
        sum(amount) as total_amount,
        sum(paid_amount) as paid_amount,
        sum(outstanding_amount) as outstanding_amount,
        sum(overdue_amount) as overdue_amount,
        sum(due_today_amount) as due_today_amount,
        sum(future_due_amount) as future_due_amount
    from {{ ref('fact_installments') }}
    group by as_of_date, currency
),

gold as (
    select
        as_of_date,
        currency,
        sum(installment_count) as installment_count,
        sum(total_amount) as total_amount,
        sum(paid_amount) as paid_amount,
        sum(outstanding_amount) as outstanding_amount,
        sum(overdue_amount) as overdue_amount,
        sum(due_today_amount) as due_today_amount,
        sum(future_due_amount) as future_due_amount
    from {{ ref('gold_ngn_collections') }}
    group by as_of_date, currency
)

select
    s.as_of_date as silver_date,
    g.as_of_date as gold_date,
    s.currency as silver_currency,
    g.currency as gold_currency
from silver s
full outer join gold g
    on s.as_of_date = g.as_of_date
    and s.currency = g.currency
where s.installment_count is distinct from g.installment_count
   or s.total_amount is distinct from g.total_amount
   or s.paid_amount is distinct from g.paid_amount
   or s.outstanding_amount is distinct from g.outstanding_amount
   or s.overdue_amount is distinct from g.overdue_amount
   or s.due_today_amount is distinct from g.due_today_amount
   or s.future_due_amount is distinct from g.future_due_amount