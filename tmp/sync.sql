/*    MotherDuck    */
select version();

use ods.daily_tracker;
attach 'src/daily_tracker/tracker.db' as local_tracker;

/* Insert into MotherDuck */
insert into ods.daily_tracker.tracker
    from local_tracker.tracker
    where date_time > (
        select max(date_time)
        from daily_tracker.tracker
    )
returning *
;


------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------

/* Compare MotherDuck and local (should be empty) */
with remote as (
    from ods.daily_tracker.tracker
    where date_time > (
        select min(date_time)
        from local_tracker.tracker
    )
)

select
    date_time,
    remote.task as task_remote,
    local.task as task_local,
    remote.detail as detail_remote,
    local.detail as detail_local,
from remote
    full join local_tracker.tracker as local
        using (date_time)
where 0=1
    or remote.task != local.task
    or remote.detail != local.detail
;


/*
start transaction;
    update ods.daily_tracker.tracker as remote
    set
        task   = local.task,
        detail = local.detail
    from local_tracker.tracker as local
    where 1=1
        and remote.date_time = local.date_time
        and (0=1
            or remote.task   != local.task
            or remote.detail != local.detail
        )
    returning *;
commit;
rollback;
*/
