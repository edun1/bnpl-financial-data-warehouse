select
    as_of_date,
    currency,
    ageing_bucket,
    count(*) as installment_count,
    count(distinct plan_id) as plan_count,
    count(distinct customer_id) as customer_count,
    sum(amount) as total_amount,
    sum(paid_amount) as paid_amount,
    sum(outstanding_amount) as outstanding_amount,
    sum(overdue_amount) as overdue_amount,
    sum(due_today_amount) as due_today_amount,
    sum(future_due_amount) as future_due_amount
from {{ ref('fact_installments') }}
group by
    as_of_date,
    currency,
    ageing_bucket