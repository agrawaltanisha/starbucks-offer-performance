import duckdb

con = duckdb.connect("starbucks.duckdb")

# 1. One row per offer received, with its window
con.sql("""
CREATE OR REPLACE TABLE instances AS
SELECT row_number() OVER (ORDER BY e.person, e.offer_id, e.hour) AS instance_id,
       e.person,
       e.offer_id,
       e.hour AS start_h,
       e.hour + CAST(o.duration AS INTEGER) * 24 AS end_h,
       o.offer_type,
       o.reward,
       o.difficulty
FROM events e
JOIN offers o ON e.offer_id = o.id
WHERE e.event = 'offer received'
""")

# 2. Match each view and completion to the latest copy of that offer
#    the customer received before it
con.sql("""
CREATE OR REPLACE TABLE matched AS
SELECT e.event, e.hour, i.instance_id, i.end_h
FROM events e
ASOF JOIN instances i
  ON e.person = i.person
 AND e.offer_id = i.offer_id
 AND e.hour >= i.start_h
WHERE e.event IN ('offer viewed', 'offer completed')
""")

# 3. First view and first completion inside each window, plus a label
con.sql("""
CREATE OR REPLACE TABLE funnel AS
SELECT *,
       CASE
         WHEN offer_type = 'informational' AND viewed_h IS NOT NULL THEN 'Viewed (informational)'
         WHEN viewed_h IS NULL AND completed_h IS NULL THEN 'Ignored'
         WHEN completed_h IS NULL THEN 'Viewed, not completed'
         WHEN viewed_h IS NOT NULL AND viewed_h <= completed_h THEN 'Completed after viewing'
         ELSE 'Completed without viewing'
       END AS outcome,
       end_h > 714 AS window_cut_off
FROM (
    SELECT i.*,
           min(m.hour) FILTER (WHERE m.event = 'offer viewed'    AND m.hour <= i.end_h) AS viewed_h,
           min(m.hour) FILTER (WHERE m.event = 'offer completed' AND m.hour <= i.end_h) AS completed_h
    FROM instances i
    LEFT JOIN matched m ON m.instance_id = i.instance_id
    GROUP BY ALL
)
""")

print("Instances (should be 76,277):")
print(con.sql("SELECT count(*) AS instances FROM funnel"))

print("Did every view and completion find an instance, and was it inside the window?")
print(con.sql("""
SELECT t.event,
       t.total_events,
       count(m.event)                                   AS matched,
       t.total_events - count(m.event)                  AS no_earlier_receive,
       count(*) FILTER (WHERE m.hour <= m.end_h)        AS inside_window,
       count(*) FILTER (WHERE m.hour >  m.end_h)        AS outside_window
FROM (SELECT event, count(*) AS total_events FROM events
      WHERE event IN ('offer viewed', 'offer completed') GROUP BY event) t
LEFT JOIN matched m ON m.event = t.event
GROUP BY t.event, t.total_events
"""))

print("Instances that got more than one completion or view (double counting):")
print(con.sql("""
SELECT event,
       count(*)     AS instances_affected,
       sum(n - 1)   AS extra_events
FROM (
    SELECT event, instance_id, count(*) AS n
    FROM matched
    WHERE hour <= end_h
    GROUP BY event, instance_id
    HAVING count(*) > 1
)
GROUP BY event
"""))

print("Outcomes by offer type:")
print(con.sql("""
SELECT offer_type, outcome, count(*) AS instances
FROM funnel
GROUP BY ALL
ORDER BY offer_type, instances DESC
"""))

print("Instances whose window runs past hour 714:")
print(con.sql("SELECT count(*) FILTER (WHERE window_cut_off) AS cut_off FROM funnel"))

con.close()
