import duckdb

con = duckdb.connect("starbucks.duckdb")

# Readable offer names stored in the database, for joining
con.sql("""
CREATE OR REPLACE TABLE offer_names AS
SELECT id AS offer_id,
       CASE offer_type WHEN 'bogo' THEN 'BOGO'
                       WHEN 'discount' THEN 'DISC'
                       ELSE 'INFO' END
       || '-' || difficulty || '-' || CAST(duration AS INTEGER) || 'd-' ||
       CASE WHEN len(channels) = 4 THEN 'all'
            WHEN len(channels) = 2 THEN array_to_string(channels, '+')
            WHEN NOT list_contains(channels, 'web') THEN 'noweb'
            WHEN NOT list_contains(channels, 'social') THEN 'nosocial'
            ELSE 'other' END AS offer_name,
       channels
FROM offers
""")

print("Overall: how much of the completions and reward money was wasted")
print(con.sql("""
SELECT
  count(*) FILTER (WHERE completed_h IS NOT NULL)                   AS completions,
  count(*) FILTER (WHERE outcome = 'Completed without viewing')     AS wasted_completions,
  round(100.0 * wasted_completions / completions, 1)                AS wasted_pct,
  sum(reward) FILTER (WHERE completed_h IS NOT NULL)                AS total_reward,
  sum(reward) FILTER (WHERE outcome = 'Completed without viewing')  AS wasted_reward,
  round(100.0 * wasted_reward / total_reward, 1)                    AS wasted_reward_pct
FROM funnel
"""))

print("Checks 4 and 5: never viewed vs viewed only after completing")
print(con.sql("""
SELECT CASE WHEN viewed_h IS NULL THEN 'Never viewed in window'
            ELSE 'Viewed only after completing' END AS kind,
       count(*)    AS completions,
       sum(reward) AS reward
FROM funnel
WHERE outcome = 'Completed without viewing'
GROUP BY kind
"""))

by_offer = con.sql("""
SELECT n.offer_name,
       f.offer_type,
       count(*)                                                         AS received,
       count(*) FILTER (WHERE viewed_h IS NOT NULL)                     AS viewed,
       round(100.0 * viewed / received, 1)                              AS view_rate_pct,
       count(*) FILTER (WHERE outcome = 'Completed after viewing')      AS wins,
       round(100.0 * wins / received, 1)                                AS win_rate_pct,
       count(*) FILTER (WHERE completed_h IS NOT NULL)                  AS completions,
       count(*) FILTER (WHERE outcome = 'Completed without viewing')    AS wasted,
       round(100.0 * wasted / completions, 1)                           AS wasted_pct,
       sum(reward) FILTER (WHERE outcome = 'Completed without viewing') AS wasted_reward,
       sum(reward) FILTER (WHERE completed_h IS NOT NULL)               AS total_reward
FROM funnel f
JOIN offer_names n USING (offer_id)
WHERE f.offer_type <> 'informational'
GROUP BY ALL
ORDER BY wasted_reward DESC
""")
print("By offer (most wasted reward first):")
print(by_offer)

print("By channel: does including a channel change the waste?")
print(con.sql("""
SELECT channel, included,
       count(*) FILTER (WHERE completed_h IS NOT NULL)               AS completions,
       count(*) FILTER (WHERE outcome = 'Completed without viewing') AS wasted,
       round(100.0 * wasted / completions, 1)                        AS wasted_pct,
       round(100.0 * count(*) FILTER (WHERE viewed_h IS NOT NULL) / count(*), 1) AS view_rate_pct
FROM (
    SELECT f.*, c.channel,
           CASE WHEN list_contains(n.channels, c.channel) THEN 'Yes' ELSE 'No' END AS included
    FROM funnel f
    JOIN offer_names n USING (offer_id)
    CROSS JOIN (VALUES ('social'), ('web'), ('mobile')) c(channel)
    WHERE f.offer_type <> 'informational'
)
GROUP BY channel, included
ORDER BY channel, included
"""))

print("Do the cut-off offers change the win rate?")
print(con.sql("""
SELECT window_cut_off,
       count(*) AS instances,
       round(100.0 * count(*) FILTER (WHERE outcome = 'Completed after viewing') / count(*), 1) AS win_rate_pct
FROM funnel
WHERE offer_type <> 'informational'
GROUP BY window_cut_off
"""))

by_offer.df().to_excel("outputs/funnel_by_offer.xlsx", index=False)
print("Saved to outputs/funnel_by_offer.xlsx")

con.close()
