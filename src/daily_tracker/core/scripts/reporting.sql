
/*
    + daily_summary +
    The daily summary of tracker records.
*/
drop view if exists daily_summary;
create view daily_summary as
    with
        daily_summary as (
            select
                date(date_time, 'weekday 0', '-6 days') as week_date,
                date(date_time) as task_date,
                task,
                sum(interval) as total_interval_daily
            from tracker
            group by
                date(date_time, 'weekday 0', '-6 days'),
                date(date_time),
                task
        ),
        weekly_summary as (
            select
                week_date,
                task,
                iif(
                    row_number() over(
                        partition by week_date
                        order by total_interval_weekly desc, task
                    ) < 8,
                    0, 1
                ) as others_flag
            from (
                select
                    week_date,
                    task,
                    sum(total_interval_daily) as total_interval_weekly
                from daily_summary
                group by
                    week_date,
                    task
            ) as weekly_raw
        )

    select
        ds.week_date,
        ds.task_date,
        iif(ws.others_flag = 1, 'Others', ds.task) as task,
        sum(ds.total_interval_daily) as total_interval
    from daily_summary as ds
        left join weekly_summary as ws
            using(week_date, task)
    group by
        ds.week_date,
        ds.task_date,
        iif(ws.others_flag = 1, 'Others', ds.task)
;


/*
    + tasks_from_yesterday +
    The tasks and their detail from "yesterday", with yesterday defined as today
    minus 1 working day so that Monday shows the details from a previous Friday.
*/
drop view if exists tasks_from_yesterday;
create view tasks_from_yesterday as
    select
        date_time,
        task,
        detail,
        interval
    from tracker
    where date(date_time) = (
        select date(max(date_time))
        from tracker
        where date_time < current_date
    )
    order by date_time desc
;


/*
    + tasks_from_yesterday_rollup +
    A rolled-up version of `tasks_from_yesterday` for a simplified view.
*/
drop view if exists tasks_from_yesterday_rollup;
create view tasks_from_yesterday_rollup as
        select
            task,
            detail,
            sum(interval) as minutes,
            printf('%.*c', sum(interval) / 15, '*') as chart
        from tasks_from_yesterday
        where task != 'Lunch Break'
        group by task, detail
    union all
        select
            null,
            null,
            sum(interval) as minutes,
            cast(sum(interval) / 60 as text) || ' hours ' || cast(sum(interval) % 60 as text) || ' minutes' as chart
        from tasks_from_yesterday
        where task != 'Lunch Break'
    order by task nulls last, detail
;


/*
    + weekly_report +
    A 6-monthly report of time spent on tasks per week.
*/
-- DROP VIEW IF EXISTS weekly_report;
-- CREATE VIEW weekly_report AS
    with
    dates as (
        select
            /* The first Monday at least 6 months ago */
            date(date(current_timestamp, '-6 months'), 'weekday 0', '-6 days') as from_date
    ),
    axis as (
            select from_date as week_starting
            from dates
        union all
            select date(week_starting, '+7 days')
            from axis
            where week_starting < date(current_date, '-7 days')
    ),

    records as (
        select
            date(date_time, 'weekday 0', '-6 days') as week_starting,
            sum(interval) as total_interval
        from main.tracker
        where date_time > (select from_date from dates)
          and task != 'Lunch Break'
        GROUP BY DATE(date_time, 'weekday 0', '-6 days')
    ),

    weekly_aggregates AS (
        SELECT
            week_starting,
            COALESCE(records.total_interval, 0) AS total_interval,
            37 * 2 * 60 AS fortnightly_commitment,  /* 37 hours per week, 2 week sprints */
            ''
                || (coalesce(records.total_interval, 0) / 60)
                || ' hours, '
                || (coalesce(records.total_interval, 0) % 60)
                ||' minutes'
            as time_working
        from axis
            left join records using (week_starting)
    ),
    weekly_report as (
        select
            week_starting,
            total_interval,
            time_working,
            fortnightly_commitment,
            sum(total_interval) over(
                order by week_starting rows between 1 preceding and current row
            ) as fortnightly_total,
            round(100.0 * sum(total_interval) over(
                order by week_starting rows between 1 preceding and current row
            ) / fortnightly_commitment, 2) as proportion_of_commitment
        from weekly_aggregates
    )

    select
        week_starting,
        total_interval,
        time_working,
        proportion_of_commitment,
        fortnightly_commitment,
        fortnightly_total
    from weekly_report
    order by week_starting desc
;
