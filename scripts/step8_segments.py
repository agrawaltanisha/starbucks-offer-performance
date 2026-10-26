import duckdb

con = duckdb.connect("starbucks.duckdb")

# 1. Segment columns for every customer
con.sql("""
CREATE OR REPLACE TABLE customer_segments AS
WITH c AS (
    SELECT *, strptime(CAST(became_member_on AS VARCHAR), '%Y%m%d')::DATE AS join_date
    FROM customers
),
latest AS (SELECT max(join_date) AS max_join FROM c)
SELECT c.id AS person,
       CASE WHEN income IS NULL   THEN 'Unknown'
            WHEN income <  50000  THEN 'Below 50k'
            WHEN income <  75000  THEN '50k-75k'
            WHEN income < 100000  THEN '75k-100k'
            ELSE '100k+' END AS income_band,
       CASE WHEN age = 118 THEN 'Unknown'
            WHEN age < 35  THEN 'Under 35'
            WHEN age < 55  THEN '35-54'
            ELSE '55+' END AS age_group,
       CASE WHEN date_diff('day', join_date, max_join) < 365 THEN 'Under 1 year'
            WHEN date_diff('day', join_date, max_join) < 730 THEN '1-2 years'
            ELSE '2+ years' END AS tenure
FROM c, latest
""")

print("Customers per segment:")
print(con.sql("""
SELECT 'Income' AS segment_type, income_band AS segment, count(*) AS customers FROM customer_segments GROUP BY ALL
UNION ALL
SELECT 'Age', age_group, count(*) FROM customer_segments GROUP BY ALL
UNION ALL
SELECT 'Tenure', tenure, count(*) FROM customer_segments GROUP BY ALL
ORDER BY segment_type, segment
"""))

# 2. Win rate and wasted share for every offer x segment
con.sql("""
CREATE OR REPLACE TABLE segment_stats AS
WITH seg AS (
    SELECT person, 'Income' AS segment_type, income_band AS segment FROM customer_segments
    UNION ALL SELECT person, 'Age', age_group FROM customer_segments
    UNION ALL SELECT person, 'Tenure', tenure FROM customer_segments
)
SELECT n.offer_name,
       f.offer_type,
       s.segment_type,
       s.segment,
       count(*)                                                       AS received,
       count(*) FILTER (WHERE outcome = 'Completed after viewing')    AS wins,
       round(100.0 * wins / received, 1)                              AS win_rate_pct,
       count(*) FILTER (WHERE completed_h IS NOT NULL)                AS completions,
       count(*) FILTER (WHERE outcome = 'Completed without viewing')  AS wasted,
       round(100.0 * wasted / nullif(completions, 0), 1)              AS wasted_pct,
       received >= 200                                                AS big_enough
FROM funnel f
JOIN seg s USING (person)
JOIN offer_names n USING (offer_id)
WHERE f.offer_type <> 'informational'
GROUP BY ALL
""")

print("Offer x segment cells, and how many are big enough (200+):")
print(con.sql("""
SELECT count(*) AS cells, count(*) FILTER (WHERE big_enough) AS big_enough_cells
FROM segment_stats
"""))

print("By offer type and segment (all offers of that type together):")
print(con.sql("""
SELECT offer_type, segment_type, segment,
       sum(received) AS received,
       round(100.0 * sum(wins) / sum(received), 1)      AS win_rate_pct,
       round(100.0 * sum(wasted) / sum(completions), 1) AS wasted_pct
FROM segment_stats
GROUP BY ALL
ORDER BY offer_type, segment_type, win_rate_pct DESC
"""))

print("Best and worst segment for each offer (cells with 200+ instances only):")
print(con.sql("""
SELECT offer_name,
       arg_max(segment_type || ': ' || segment, win_rate_pct) AS best_segment,
       max(win_rate_pct)                                      AS best_win_rate,
       arg_min(segment_type || ': ' || segment, win_rate_pct) AS worst_segment,
       min(win_rate_pct)                                      AS worst_win_rate,
       arg_min(wasted_pct, win_rate_pct)                      AS worst_wasted_pct
FROM segment_stats
WHERE big_enough
GROUP BY offer_name
ORDER BY offer_name
"""))

con.sql("SELECT * FROM segment_stats ORDER BY offer_name, segment_type, segment").df() \
   .to_excel("outputs/segments.xlsx", index=False)
print("Saved to outputs/segments.xlsx")

con.close() 
