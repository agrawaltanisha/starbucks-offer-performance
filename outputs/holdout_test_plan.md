# Holdout test plan: BOGO-5-7d-nosocial

## Why this offer
It has the most wasted reward of any offer: $10,985, with 51.1% of its
completions happening before the customer viewed it. Its win rate is 27.4%.

## Groups
Customers who would normally get this offer are split at random:
- 90% get the offer
- 10% get nothing (holdout)

Optional third group: the same offer sent with the social channel added,
to test the channel finding directly.

## Main metric
Average spend per customer in the 7 days after the send date.

## Guardrails
- Reward cost per customer in the offer group. Today it is $2.80
  ($21,515 reward / 7,677 sends).
- Opt-out or unsubscribe rate. It should not rise in the offer group.

## Length
2 weeks, so both weekday and weekend habits are included.

## Decision rule
Keep the offer only if the offer group's 7-day spend per customer beats
the holdout group's by more than the reward cost per customer (about $2.80).
If the gap is smaller, the offer pays out more than it brings in.

## Rollback
Stop early if reward cost per customer goes above $3.50 (25% over today's
level), or if opt-outs rise clearly above the holdout group.

## What this test answers
In the current data, customers spent $4.80 a day while a viewed offer was
running vs $1.71 with no offer. That gap may come from active customers
viewing more offers, not from the offer itself. Only a holdout group shows
the real effect.

## Before launch
Check with a sample size calculation that 10% of one send gives enough
holdout customers. If not, run the test across two sends.
