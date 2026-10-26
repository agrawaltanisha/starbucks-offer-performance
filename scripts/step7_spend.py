import duckdb

con = duckdb.connect("starbucks.duckdb")

con.sql("""
CREATE OR REPLACE TABLE person_days AS
WITH days AS (SELECT range AS day FROM range(0, 30)),
daily_spend AS (
    SELECT person, hour // 24 AS day, sum(amount) AS spend
    FROM events
    WHERE event = 'transaction'
    GROUP BY ALL
),
flags AS (
    SELECT c.id AS person, d.day,
           coalesce(bool_or(f.viewed_h IS NOT NULL AND f.viewed_h // 24 <= d.day), false) AS viewed_active,
           coalesce(bool_or(f.person IS NOT NULL), false)                                 AS any_active
    FROM customers c
    CROSS JOIN days d
    LEFT JOIN funnel f
      ON f.person = c.id
     AND f.start_h // 24 <= d.day
     AND f.end_h   // 24 >= d.day
    GROUP BY c.id, d.day
)
SELECT fl.person, fl.day,
       coalesce(s.spend, 0) AS spend,
       CASE WHEN viewed_active THEN 'Viewed offer running'
            WHEN any_active    THEN 'Offer received, not yet viewed'
            ELSE 'No active offer' END AS state
FROM flags fl
LEFT JOIN daily_spend s USING (person, day)
""")

print("Check: customer-days (should be 17,000 x 30 = 510,000)")
print(con.sql("SELECT count(*) AS person_days FROM person_days"))

print("Check: total spend matches the raw transactions")
print(con.sql("""
SELECT (SELECT round(sum(spend), 2) FROM person_days) AS spend_in_days,
       (SELECT round(sum(amount), 2) FROM events WHERE event = 'transaction') AS spend_raw
"""))

print("Average spend per customer per day, by state")
print(con.sql("""
SELECT state,
       count(*)                AS customer_days,
       round(sum(spend), 0)    AS total_spend,
       round(avg(spend), 2)    AS avg_spend_per_day,
       round(100.0 * count(*) FILTER (WHERE spend > 0) / count(*), 1) AS pct_days_with_purchase
FROM person_days
GROUP BY state
ORDER BY avg_spend_per_day DESC
"""))

con.close()
