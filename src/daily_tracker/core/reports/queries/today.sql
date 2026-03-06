-- attach 'src/daily_tracker/tracker.db' as tracker;
select
    task,
    detail,
    (to_minutes(sum(interval)::int)::text)[0:5] as duration
from tracker.tracker
where date_time::date = current_date
group by grouping sets ((task, detail), ())
order by task nulls last, detail nulls last
