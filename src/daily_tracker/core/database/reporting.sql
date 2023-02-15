
/*
    + main.daily_summary +
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
