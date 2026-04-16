-- attach 'src/daily_tracker/tracker.db' as tracker;
select
    task,
    detail,
    min(date_time) as started_at,
    max(date_time) as completed_at,
    (to_minutes(sum(interval)::int)::text)[0:-4] as duration
from tracker.tracker
where task = '{task}'
group by grouping sets ((task, detail), (task))
order by grouping_id(task, detail), started_at
