-- attach 'src/daily_tracker/tracker.db' as tracker;
with recursive

dates(from_date) as (
    select date_trunc('week', current_date - interval '6 months')
),

axis(week_starting) as (
        from dates
    union all
        select week_starting + interval '7 days'
        from axis
        where week_starting < date_trunc('week', current_date - interval '7 days')
),

records(week_starting, total_interval) as (
    select date_trunc('week', date_time), sum("interval")
    from tracker.tracker
    where 1=1
        and date_time > (select from_date from dates)
        and task != 'Lunch Break'
    group by all
),

weekly_aggregates AS (
    select
        week_starting,
        coalesce(records.total_interval, 0) AS weekly_total,
        40 * 60 AS weekly_commitment,  /* 40 hours per week */
        (''
            || floor(weekly_total / 60)::int
            || ' hours '
            || floor(weekly_total % 60)::int
            ||' minutes'
        ) as time_working,
    from axis
        left join records
            using (week_starting)
)

select
    week_starting,
    weekly_total,
    time_working,
    round(100 * weekly_total / weekly_commitment, 2) as proportion_of_commitment,
    -- weekly_commitment,
from weekly_aggregates
order by week_starting desc
