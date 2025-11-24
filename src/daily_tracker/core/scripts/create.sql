
/*
    + tracker +
    The core table in this application that holds all historic data.
*/
drop table if exists tracker;
create table tracker(
    date_time datetime not null primary key unique,
    task text not null,
    detail text not null default '',
    interval integer not null
);
create index tracker_task on tracker(task)
;


/*
    + task_last_detail +
    The latest detail per task. Used for automatically filling the detail text
    box for each task. Updates on inserts and updates of the main.tracker table.
*/
drop table if exists task_last_detail;
create table task_last_detail(
    task text not null primary key unique references tracker(task),
    detail text not null,
    last_date_time datetime not null
);


drop trigger if exists set_tracker_latest_task_on_insert;
create trigger set_tracker_latest_task_on_insert
    before insert on tracker
    begin
        insert into task_last_detail
        values (new.task, new.detail, new.date_time)
        on conflict(task) do update
        set detail = new.detail,
            last_date_time = new.date_time
        ;
    end
;

drop trigger if exists set_tracker_latest_task_on_update;
create trigger set_tracker_latest_task_on_update
    before update on tracker
    begin
        insert into task_last_detail
        values (new.task, new.detail, new.date_time)
        on conflict(task) do update
        set detail = new.detail,
            last_date_time = new.date_time
        ;
    end
;


/*
    + default_tasks +
    The default tasks used to populate the task input box drop-down. This
    should be configurable outside of this module.
*/
drop table if exists default_tasks;
create table default_tasks(
    task text not null unique
);
insert into default_tasks
values
    ('Lunch Break'),
    ('Meetings'),
    ('Housekeeping'),
    ('Adhoc Chat'),
    ('Adhoc Task'),
    ('Documentation'),
    ('Personal Development'),
    ('Unable to Work')
;
insert into task_last_detail(task, detail, last_date_time)
    select
        task,
        '',
        ''
from default_tasks
;


/*
    + task_detail_with_defaults +
    The latest detail per task.
*/
drop view if exists task_detail_with_defaults;
create view task_detail_with_defaults as
    with defaults as (
        select
            dt.task,
            tld.detail,
            coalesce(nullif(tld.last_date_time, ''), '9999-12-31 00:00:00') as last_date_time
        from default_tasks as dt
            left join task_last_detail as tld using(task)
    )

        select
            0 as indx,
            task,
            detail,
            last_date_time
        from defaults
    union
        select
            1 as indx,
            task,
            detail,
            last_date_time
        from task_last_detail
        where task not in (select task from defaults)
;


/* Command to validate the objects in the database */
pragma quick_check;
