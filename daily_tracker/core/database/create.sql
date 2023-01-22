
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
    WHERE date_time >= IIF(
        STRFTIME('%w', DATE('now')) = '1', /* Monday */
        DATE('now', '-3 day'),
        DATE('now', '-1 day')
    )
    ORDER BY date_time DESC
;
