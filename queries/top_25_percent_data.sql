WITH daily_position AS (
    SELECT 
        p.date,
        p.company_id,
        p.shares,
        pr.close_usd,
        p.shares * pr.close_usd AS daily_position_usd
    FROM
        POSITION p
    JOIN 
        PRICE pr
    ON p.company_id = pr.company_id AND p.date = pr.date
),
-- last year's average position for each company
last_year_avg_position AS (
    SELECT 
        company_id,
        avg(daily_position_usd) AS avg_position
    FROM 
        daily_position dp
    WHERE 
        date >= dateadd(year,-1, current_date())
    GROUP BY
        company_id
),
-- ranking companies based on last year's avg position
ranked_companies AS (
    SELECT
        company_id,
        avg_position,
        NTILE(4) OVER (ORDER BY avg_position DESC) AS quartile -- already partitioned by companyies
    FROM
        last_year_avg_position
),
top_25_percent AS (
    SELECT 
        company_id,
        avg_position,
    FROM
        ranked_companies
    WHERE 
        quartile = 1
),
latest_data AS (
    SELECT
        dp.company_id,
        dp.shares,
        dp.close_usd,
        dp.date,
        ROW_NUMBER() OVER (PARTITION BY dp.company_id ORDER BY dp.date DESC) as rn
    FROM 
        daily_position dp
    JOIN
        top_25_percent t ON dp.company_id = t.company_id
        
)
-- top 25 data% 
SELECT
    c.TICKER,
    c.sector_name,
    ld.shares,
    ld.close_usd AS last_close_price_usd,
    t.avg_position AS average_position_last_year
FROM 
    top_25_percent t
JOIN 
    CODE_CHALLENGE_ZHEWNTMM.SOURCE.COMPANY c ON  t.company_id = c.id
JOIN 
    latest_data ld ON t.company_id = ld.company_id
WHERE 
    ld.rn = 1
ORDER BY 
    t.avg_position DESC;
