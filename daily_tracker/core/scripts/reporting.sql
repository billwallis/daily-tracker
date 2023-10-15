
/*
    + daily_summary +
    The daily summary of tracker records.
*/
DROP VIEW IF EXISTS daily_summary;
CREATE VIEW daily_summary AS
    WITH
        daily_summary AS (
            SELECT
                DATE(date_time, 'weekday 0', '-6 days') AS week_date,
                DATE(date_time) AS task_date,
                task,
                SUM(interval) AS total_interval_daily
            FROM tracker
            GROUP BY
                DATE(date_time, 'weekday 0', '-6 days'),
                DATE(date_time),
                task
        ),
        weekly_summary AS (
            SELECT
                week_date,
                task,
                IIF(
                    ROW_NUMBER() OVER(
                        PARTITION BY week_date
                        ORDER BY total_interval_weekly DESC, task
                    ) < 8,
                    0, 1
                ) AS others_flag
            FROM (
                SELECT
                    week_date,
                    task,
                    SUM(total_interval_daily) AS total_interval_weekly
                FROM daily_summary
                GROUP BY
                    week_date,
                    task
            ) AS weekly_raw
        )

    SELECT
        ds.week_date,
        ds.task_date,
        IIF(ws.others_flag = 1, 'Others', ds.task) AS task,
        SUM(ds.total_interval_daily) AS total_interval
    FROM daily_summary AS ds
        LEFT JOIN weekly_summary AS ws
            USING(week_date, task)
    GROUP BY
        ds.week_date,
        ds.task_date,
        IIF(ws.others_flag = 1, 'Others', ds.task)
;


/*
    + tasks_from_yesterday +
    The tasks and their detail from "yesterday", with yesterday defined as today
    minus 1 working day so that Monday shows the details from a previous Friday.
*/
DROP VIEW IF EXISTS tasks_from_yesterday;
CREATE VIEW tasks_from_yesterday AS
    SELECT
        date_time,
        task,
        detail,
        interval
    FROM tracker
    WHERE DATE(date_time) = (
        SELECT DATE(MAX(date_time))
        FROM tracker
        WHERE date_time < CURRENT_DATE
    )
    ORDER BY date_time DESC
;


/*
    + tasks_from_yesterday_rollup +
    A rolled-up version of `tasks_from_yesterday` for a simplified view.
*/
DROP VIEW IF EXISTS tasks_from_yesterday_rollup;
CREATE VIEW tasks_from_yesterday_rollup AS
    SELECT
        task,
        detail,
        SUM(interval) AS minutes,
        PRINTF('%.*c', SUM(interval) / 15, '*') AS chart
    FROM tasks_from_yesterday
    WHERE task != 'Lunch Break'
    GROUP BY task, detail
    ORDER BY task, detail
;


/*
    + weekly_report +
    A 6-monthly report of time spent on tasks per week.
*/
-- DROP VIEW IF EXISTS weekly_report;
-- CREATE VIEW weekly_report AS
    WITH
    dates AS (
        SELECT
            /* The first Monday at least 6 months ago */
            DATE(DATE(CURRENT_TIMESTAMP, '-6 months'), 'weekday 0', '-6 days') AS from_date
    ),
    axis AS (
            SELECT from_date AS week_starting
            FROM dates
        UNION ALL
            SELECT DATE(week_starting, '+7 days')
            FROM axis
            WHERE week_starting < DATE(CURRENT_DATE, '-7 days')
    ),

    records AS (
        SELECT
            DATE(date_time, 'weekday 0', '-6 days') AS week_starting,
            SUM(interval) AS total_interval
        FROM main.tracker
        WHERE date_time > (SELECT from_date FROM dates)
          AND task != 'Lunch Break'
        GROUP BY DATE(date_time, 'weekday 0', '-6 days')
    ),

    weekly_aggregates AS (
        SELECT
            week_starting,
            COALESCE(records.total_interval, 0) AS total_interval,
            37 * 2 * 60 AS fortnightly_commitment,  /* 37 hours per week, 2 week sprints */
            ''
                || (COALESCE(records.total_interval, 0) / 60)
                || ' hours, '
                || (COALESCE(records.total_interval, 0) % 60)
                ||' minutes'
            AS TIME_WORKING
        FROM axis
            LEFT JOIN records USING (week_starting)
    ),
    weekly_report AS (
        SELECT
            week_starting,
            total_interval,
            time_working,
            fortnightly_commitment,
            SUM(total_interval) OVER(
                ORDER BY week_starting ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
            ) AS fortnightly_total,
            ROUND(100.0 * SUM(total_interval) OVER(
                ORDER BY week_starting ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
            ) / fortnightly_commitment, 2) AS proportion_of_commitment
        FROM weekly_aggregates
    )

    SELECT
        week_starting,
        total_interval,
        time_working,
        proportion_of_commitment,
        fortnightly_commitment,
        fortnightly_total
    FROM weekly_report
    ORDER BY week_starting DESC
;
