/*    SQLite    */
select sqlite_version();

--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

/* Copy previous */
insert into tracker (date_time, task, detail, interval)
    select
        datetime(date_time, '+15 minutes'),
--         datetime('2026-05-18 19:30:00'),
        task,
        detail,
        interval
    from tracker
    where date_time = (select max(date_time) from tracker)
returning *
;

/* Add entry */
insert into tracker (date_time, task, detail, interval)
values
    (
        datetime('2026-01-30 08:00:00'),
        'Documentation',
        'Onboarding',
        15
    )
returning *
;

/* Add daily entry */
insert into tracker (date_time, task, detail, interval)
values
    (
        datetime('2025-12-05 09:00:00'),
        'Documentation',
        'Onboarding',
        (60 * 8)
    )
returning *
;


--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

/* Get recent things */
select task, detail
from tracker
group by task, detail
order by max(date_time) desc
limit 20
;

/* Rename something (task + detail) */
begin transaction;
    update tracker
    set
        task = 'Documentation',
        detail = 'Doing another thing'
    where 1=1
        and task = 'Documentation'
        and detail = 'Doing a thing'
    returning *
    ;
rollback;
commit;
/* Rename something (task only) */
begin transaction;
    update tracker
    set task = 'New name'
    where task = 'Rename this'
    returning *
    ;
rollback;
commit;

/* Delete recent references if task no longer exists */
delete from task_last_detail
where not exists(
    select *
    from tracker
    where task_last_detail.task = tracker.task
)
returning *
;
