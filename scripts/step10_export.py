import duckdb

con = duckdb.connect("starbucks.duckdb")

raw = con.sql("""
SELECT n.offer_name                                   AS "Offer",
       f.offer_type                                   AS "Offer type",
       CASE WHEN list_contains(n.channels, 'social') THEN 'Yes' ELSE 'No' END AS "Social",
       CASE WHEN list_contains(n.channels, 'web')    THEN 'Yes' ELSE 'No' END AS "Web",
       CASE WHEN list_contains(n.channels, 'mobile') THEN 'Yes' ELSE 'No' END AS "Mobile",
       s.income_band                                  AS "Income band",
       s.age_group                                    AS "Age group",
       s.tenure                                       AS "Tenure",
       f.outcome                                      AS "Outcome",
       CASE WHEN f.viewed_h IS NOT NULL THEN 1 ELSE 0 END                     AS "Viewed",
       CASE WHEN f.outcome = 'Completed after viewing' THEN 1 ELSE 0 END      AS "Win",
       CASE WHEN f.outcome = 'Completed without viewing' THEN 1 ELSE 0 END    AS "Wasted",
       CASE WHEN f.outcome = 'Completed without viewing' THEN f.reward ELSE 0 END AS "Wasted reward"
FROM funnel f
JOIN offer_names n USING (offer_id)
JOIN customer_segments s USING (person)
""")

print(con.sql("SELECT count(*) AS rows, sum(\"Wasted reward\") AS wasted_reward FROM raw"))
raw.df().to_excel("outputs/raw_data.xlsx", index=False)
print("Saved to outputs/raw_data.xlsx")
con.close()
