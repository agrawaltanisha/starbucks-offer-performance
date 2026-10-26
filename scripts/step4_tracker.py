import duckdb

con = duckdb.connect("starbucks.duckdb")

tracker = con.sql("""
WITH sent AS (
    SELECT offer_id, count(*) AS times_sent
    FROM events
    WHERE event = 'offer received'
    GROUP BY offer_id
)
SELECT
    CASE offer_type WHEN 'bogo' THEN 'BOGO'
                    WHEN 'discount' THEN 'DISC'
                    ELSE 'INFO' END
    || '-' || difficulty || '-' || CAST(duration AS INTEGER) || 'd-' ||
    CASE WHEN len(channels) = 4 THEN 'all'
         WHEN len(channels) = 2 THEN array_to_string(channels, '+')
         WHEN NOT list_contains(channels, 'web') THEN 'noweb'
         WHEN NOT list_contains(channels, 'social') THEN 'nosocial'
         ELSE 'other' END                             AS "Offer name",
    id                                                AS "Offer ID",
    offer_type                                        AS "Type",
    difficulty                                        AS "Min spend",
    reward                                            AS "Reward",
    CAST(duration AS INTEGER)                         AS "Duration (days)",
    CASE WHEN list_contains(channels, 'email')  THEN 'Yes' ELSE 'No' END AS "Email",
    CASE WHEN list_contains(channels, 'mobile') THEN 'Yes' ELSE 'No' END AS "Mobile",
    CASE WHEN list_contains(channels, 'social') THEN 'Yes' ELSE 'No' END AS "Social",
    CASE WHEN list_contains(channels, 'web')    THEN 'Yes' ELSE 'No' END AS "Web",
    s.times_sent                                      AS "Times sent",
    'Active'                                          AS "Status",
    ''                                                AS "Notes"
FROM offers o
LEFT JOIN sent s ON s.offer_id = o.id
ORDER BY offer_type, difficulty, duration
""")

print(tracker)

tracker.df().to_excel("outputs/offer_tracker.xlsx", index=False)
print("Saved to outputs/offer_tracker.xlsx")

con.close()
