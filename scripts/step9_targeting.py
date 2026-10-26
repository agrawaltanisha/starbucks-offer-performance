import duckdb

con = duckdb.connect("starbucks.duckdb")

print("By offer type and segment (full table):")
print(con.sql("""
SELECT offer_type, segment_type, segment,
       sum(received) AS received,
       round(100.0 * sum(wins) / sum(received), 1)      AS win_rate_pct,
       round(100.0 * sum(wasted) / sum(completions), 1) AS wasted_pct
FROM segment_stats
GROUP BY ALL
ORDER BY offer_type, segment_type, win_rate_pct DESC
""").df().to_string(index=False))

print("\nBest and worst KNOWN segment for each offer (Unknown left out):")
print(con.sql("""
SELECT offer_name,
       arg_max(segment_type || ': ' || segment, win_rate_pct) AS best_segment,
       max(win_rate_pct)                                      AS best_win,
       arg_max(wasted_pct, win_rate_pct)                      AS best_wasted,
       arg_min(segment_type || ': ' || segment, win_rate_pct) AS worst_segment,
       min(win_rate_pct)                                      AS worst_win,
       arg_min(wasted_pct, win_rate_pct)                      AS worst_wasted
FROM segment_stats
WHERE big_enough AND segment <> 'Unknown'
GROUP BY offer_name
ORDER BY offer_name
""").df().to_string(index=False))

print("\nThe Unknown group, offer by offer:")
print(con.sql("""
SELECT offer_name, received, win_rate_pct, wasted_pct
FROM segment_stats
WHERE segment = 'Unknown' AND segment_type = 'Income'
ORDER BY offer_name
""").df().to_string(index=False))

con.close()
