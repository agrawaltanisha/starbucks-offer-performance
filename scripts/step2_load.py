import duckdb

con = duckdb.connect("starbucks.duckdb")

con.sql("CREATE OR REPLACE TABLE offers AS SELECT * FROM read_json_auto('data/portfolio.json')")
con.sql("CREATE OR REPLACE TABLE customers AS SELECT * FROM read_json_auto('data/profile.json')")
con.sql("CREATE OR REPLACE TABLE raw_events AS SELECT * FROM read_json_auto('data/transcript.json', sample_size=-1)")

print("How DuckDB read the events file:")
print(con.sql("DESCRIBE raw_events"))

con.sql("""
CREATE OR REPLACE TABLE events AS
SELECT person,
       event,
       time AS hour,
       coalesce(value['offer id'], value['offer_id']) AS offer_id,
       value['amount'] AS amount,
       value['reward'] AS reward_paid
FROM raw_events
""")

print("Events per type, and how many have an offer ID:")
print(con.sql("""
SELECT event, count(*) AS n, count(offer_id) AS with_offer_id
FROM events GROUP BY event ORDER BY n DESC
"""))

print("Which spelling of the offer ID key each event type uses:")
print(con.sql("""
SELECT event,
       count(value['offer id']) AS with_space,
       count(value['offer_id']) AS with_underscore
FROM raw_events
WHERE event LIKE 'offer%'
GROUP BY event
"""))

con.close()
