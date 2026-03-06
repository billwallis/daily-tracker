-- attach 'src/daily_tracker/tracker.db' as tracker;
with

day_axis as (
    select
        dt::date as work_date,
        dayname(work_date) as weekday,
        if(weekday in ('Saturday', 'Sunday'), 0, 8) as daily_commitment,
    from generate_series(
        current_date,
        current_date - interval '21 days',
        interval '-1 day'
    ) as gs(dt)
),

daily_summary as (
    select
        date_time::date as work_date,
        sum(interval) as total_minutes
    from tracker.tracker
    where 1=1
        and date_time::date >= (select min(work_date) from day_axis)
        and task != 'Lunch Break'
    group by work_date
),

daily_capacity as (
    select
        day_axis.work_date,
        day_axis.weekday,
        day_axis.daily_commitment,
        coalesce(daily_summary.total_minutes, 0) as total_minutes,
    from day_axis
        left join daily_summary
            using (work_date)
    where day_axis.work_date <= current_date
)

select
    work_date,
    weekday,
    total_minutes,
    (''
        || lpad(floor(total_minutes / 60)::int::text, 2, ' ')
        || ' hours '
        || lpad(floor(total_minutes % 60)::int::text, 2, ' ')
        ||' minutes'
    ) as hours_worked,
    if(
        daily_commitment = 0,
        null,
        100 * total_minutes / (daily_commitment * 60.0)
    )::numeric(5, 2) as proportion_of_commitment,
from daily_capacity
order by work_date
