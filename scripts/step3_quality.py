import duckdb

con = duckdb.connect("starbucks.duckdb")

print("Check 1: placeholder ages (age = 118)")
print(con.sql("""
SELECT count(*) AS age_118,
       count(*) FILTER (WHERE income IS NULL) AS also_no_income,
       count(*) FILTER (WHERE gender IS NULL) AS also_no_gender
FROM customers WHERE age = 118
"""))

print("Are there missing incomes outside the age-118 group?")
print(con.sql("""
SELECT count(*) AS missing_income_other_ages
FROM customers WHERE income IS NULL AND age <> 118
"""))

print("Check 3: duplicate offer events (same person, event, offer, hour)")
print(con.sql("""
SELECT event, count(*) AS duplicate_groups, sum(n - 1) AS extra_rows
FROM (
    SELECT person, event, offer_id, hour, count(*) AS n
    FROM events
    WHERE event <> 'transaction'
    GROUP BY ALL
    HAVING count(*) > 1
)
GROUP BY event
"""))

print("Check 8: completions by offer type (informational should be 0)")
print(con.sql("""
SELECT o.offer_type, count(*) AS completions
FROM events e JOIN offers o ON e.offer_id = o.id
WHERE e.event = 'offer completed'
GROUP BY o.offer_type
"""))

print("Extra: offer IDs in events that don't exist in the offers table")
print(con.sql("""
SELECT count(*) AS unknown_offer_events
FROM events
WHERE offer_id IS NOT NULL AND offer_id NOT IN (SELECT id FROM offers)
"""))

print("Extra: people in events who aren't in the customers table")
print(con.sql("""
SELECT count(DISTINCT person) AS unknown_people
FROM events
WHERE person NOT IN (SELECT id FROM customers)
"""))

print("Extra: time range of the test, in hours")
print(con.sql("SELECT min(hour) AS first_hour, max(hour) AS last_hour FROM events"))

con.close()

