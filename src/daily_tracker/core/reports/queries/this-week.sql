-- attach 'src/daily_tracker/tracker.db' as tracker;
select
    date_time::date as "date",
    task,
    detail,
    (to_minutes(sum(interval)::int)::text)[0:-4] as duration
from tracker.tracker
where 1=1
    and task not in ('Lunch Break', 'Unable to Work')
    and date_trunc('week', date_time::date) = date_trunc('week', current_date)
group by grouping sets (
    ("date", task, detail),
    ("date"),
    ()
)
order by "date", task nulls last, detail nulls last
