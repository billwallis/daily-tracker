
/*
    + main.tracker +
    The core table in this application that holds all historic data.
*/
DROP TABLE IF EXISTS tracker;
CREATE TABLE tracker(
    date_time DATETIME NOT NULL PRIMARY KEY UNIQUE,
    task TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    interval INTEGER NOT NULL
);
CREATE INDEX tracker_task
    ON tracker(task)
;


/*
    + main.task_last_detail +
    The latest detail per task. Used for automatically filling the detail text
    box for each task. Updates on inserts and updates of the main.tracker table.
*/
DROP TABLE IF EXISTS task_last_detail;
CREATE TABLE task_last_detail(
    task TEXT NOT NULL PRIMARY KEY UNIQUE REFERENCES tracker(task),
    detail TEXT NOT NULL,
    last_date_time DATETIME NOT NULL
);


DROP TRIGGER IF EXISTS set_tracker_latest_task_on_insert;
CREATE TRIGGER set_tracker_latest_task_on_insert
    BEFORE INSERT ON tracker
BEGIN
    INSERT INTO task_last_detail
    VALUES (NEW.task, NEW.detail, NEW.date_time)
    ON CONFLICT(task) DO UPDATE
    SET detail = NEW.detail,
        last_date_time = NEW.date_time
    ;
END
;

DROP TRIGGER IF EXISTS set_tracker_latest_task_on_update;
CREATE TRIGGER set_tracker_latest_task_on_update
    BEFORE UPDATE ON tracker
BEGIN
    INSERT INTO task_last_detail
    VALUES (NEW.task, NEW.detail, NEW.date_time)
    ON CONFLICT(task) DO UPDATE
    SET detail = NEW.detail,
        last_date_time = NEW.date_time
    ;
END
;


/*
    + main.default_tasks +
    The default tasks used to populate the task input box drop-down. This should
    be configurable outside of this module.
*/
DROP TABLE IF EXISTS default_tasks;
CREATE TABLE default_tasks(
    task TEXT NOT NULL UNIQUE
);
INSERT INTO default_tasks
VALUES
    ('Lunch Break'),
    ('Meetings'),
    ('Housekeeping'),
    ('Adhoc Chat'),
    ('Adhoc Task'),
    ('Documentation'),
    ('Personal Development'),
    ('Unable to Work')
;
INSERT INTO task_last_detail(task, detail, last_date_time)
    SELECT
        task,
        '',
        ''
FROM default_tasks
;


/*
    + main.tracker_latest_task +
    The latest detail per task over the last 14 days.
*/
DROP VIEW IF EXISTS task_detail_with_defaults;
CREATE VIEW task_detail_with_defaults AS
    WITH defaults AS (
        SELECT
            dt.task,
            tld.detail,
            COALESCE(NULLIF(tld.last_date_time, ''), '9999-12-31 00:00:00') AS last_date_time
        FROM default_tasks AS dt
            LEFT JOIN task_last_detail AS tld USING(task)
    )

        SELECT
            0 AS indx,
            task,
            detail,
            last_date_time
        FROM defaults
    UNION
        SELECT
            1 AS indx,
            task,
            detail,
            last_date_time
        FROM task_last_detail
        WHERE task NOT IN (SELECT task FROM defaults)
;


/*
    + main.tasks_from_yesterday +
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
