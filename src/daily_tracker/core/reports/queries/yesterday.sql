select
    task,
    detail,
    (to_minutes(sum(interval)::int)::text)[0:5] as duration
from tracker.tracker
where 1=1
    and task != 'Lunch Break'
    and date_time::date = (
        select max(date_time::date)
        from tracker.tracker
        where date_time::date < current_date
    )
group by grouping sets ((task, detail), ())
order by task nulls last, detail nulls last
