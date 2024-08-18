WITH starting_date AS (
    SELECT MIN(p.date) AS min_date
    FROM position p
    JOIN price pr ON p.date = pr.date
),
date_range AS (
    -- start date
    SELECT sd.min_date as dt
    FROM starting_date sd
    UNION ALL
    --new calculated date becomes the dt for the next iteration
    SELECT DATEADD('day',1,dt) as dt
    FROM date_range
    -- end date (inclusive)
    WHERE dt < current_date()
),
filled_data AS (
    SELECT 
        dr.dt AS date,
        c.ID AS COMPANY_ID,
        c.SECTOR_NAME,
        p.shares,
        LAST_VALUE(p.SHARES IGNORE NULLS) OVER (
            PARTITION BY c.ID ORDER BY dr.dt
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS filled_shares,
        pr.close_usd,
        LAST_VALUE(pr.CLOSE_USD IGNORE NULLS) OVER (
            PARTITION BY c.ID ORDER BY dr.dt
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS filled_price_usd
    FROM date_range dr
    CROSS JOIN company c
    LEFT JOIN position p ON dr.dt = p.DATE AND c.ID = p.COMPANY_ID
    LEFT JOIN price pr ON dr.dt = pr.DATE AND c.ID = pr.COMPANY_ID
),
company_position AS (
    SELECT
        date,
        COMPANY_ID,
        SECTOR_NAME,
        filled_shares,
        filled_price_usd,
        COALESCE(filled_shares * filled_price_usd, 0) AS position_usd
    FROM filled_data
    WHERE filled_shares IS NOT NULL AND filled_price_usd IS NOT NULL
),
sector_position AS (
    SELECT 
        date,
        SECTOR_NAME,
        SUM(position_usd) AS sector_position_usd
    FROM company_position
    GROUP BY date, SECTOR_NAME
),
latest_date AS (
    SELECT MAX(date) AS max_date
    FROM sector_position
),
top_10_sectors AS (
    SELECT 
        sp.SECTOR_NAME,
        sp.sector_position_usd
    FROM sector_position sp
    JOIN latest_date ld ON sp.date = ld.max_date
    ORDER BY sp.sector_position_usd DESC
    LIMIT 10
)
SELECT 
    SECTOR_NAME,
    sector_position_usd
FROM top_10_sectors
ORDER BY sector_position_usd DESC;

