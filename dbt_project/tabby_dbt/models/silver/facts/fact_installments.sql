with installments as (
    select * from {{ ref('stg_installments') }}
),

plans as (
    select * from {{ ref('stg_payment_plans') }}
),

joined as (
    select
        i.installment_id,
        i.plan_id,
        p.transaction_id,
        p.customer_id,
        p.merchant_id,
        i.installment_number,
        i.amount,
        i.due_date,
        i.paid_date,
        i.status as source_status,
        p.currency,
        p.as_of_date,
        case
            when i.paid_date <= p.as_of_date then true
            else false
        end as is_paid
    from installments i
    left join plans p on i.plan_id = p.plan_id
),

balances as (
    select
        *,
        case when is_paid then amount else 0 end
            as paid_amount,
        case when not is_paid then amount else 0 end
            as outstanding_amount,
        case
            when not is_paid and due_date < as_of_date
            then amount else 0
        end as overdue_amount,
        case
            when not is_paid and due_date = as_of_date
            then amount else 0
        end as due_today_amount,
        case
            when not is_paid and due_date > as_of_date
            then amount else 0
        end as future_due_amount,
        case
            when not is_paid and due_date < as_of_date
            then date_diff('day', due_date, as_of_date)
            else 0
        end as days_past_due
    from joined
)

select
    *,
    case
        when is_paid then 'Paid'
        when due_date > as_of_date then 'Not yet due'
        when due_date = as_of_date then 'Due today'
        when days_past_due between 1 and 30 then '1-30 days'
        when days_past_due between 31 and 60 then '31-60 days'
        when days_past_due between 61 and 90 then '61-90 days'
        when days_past_due > 90 then '91+ days'
        else 'Unknown'
    end as ageing_bucket
from balances