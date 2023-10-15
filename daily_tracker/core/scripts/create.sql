
/*
    + tracker +
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
    + task_last_detail +
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
    + default_tasks +
    The default tasks used to populate the task input box drop-down. This
    should be configurable outside of this module.
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
    + task_detail_with_defaults +
    The latest detail per task.
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


------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------

/* Dirty hack -- the triggers are breaking in the sqlite3 API */
DROP VIEW v_latest_tasks;
CREATE VIEW v_latest_tasks AS
    SELECT
        CASE WHEN task IN (SELECT task FROM default_tasks) THEN 0 ELSE 1 END AS indx,
        MAX(date_time) AS last_date_time,
        task,
        detail
    FROM tracker
    GROUP BY task
;


/* Example usage */
SELECT *
FROM v_latest_tasks
WHERE last_date_time >= DATETIME('now', :date_modifier)
  OR indx = 0  /* Defaults */
ORDER BY indx, task
;


/* Command to validate the objects in the database */
PRAGMA quick_check;
