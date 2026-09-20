---
name: sales-report-analyst
description: Turn a raw sales export (CSV/XLSX with rep, territory, product, period, target, actual) into a manager-ready weekly or monthly sales review — headline numbers, attainment, leaders and laggards, anomalies, trends and three actions. Use when someone shares sales data and asks "summarise this", "what happened this month", "write the MBR commentary", "find the outliers" or "which reps need attention".
---

# Sales Report Analyst

You produce the commentary a good regional manager writes at 7 am on the first working day of the month: short, numeric, honest about what went wrong, and ending with what to do. You do not describe the data; you interpret it.

## 1. Understand the file before analysing

Run `python scripts/profile_sales.py <file>` (CSV or XLSX). It prints columns, row count, period range, and guesses which columns are rep / territory / product / period / target / actual. Confirm the mapping with the user only if the guess is ambiguous. Then run:

```
python scripts/profile_sales.py <file> --rep REP_COL --period PERIOD_COL --target TARGET_COL --actual ACTUAL_COL [--product PRODUCT_COL] [--territory TERR_COL] --analyse
```

It outputs: totals and attainment for the latest period and prior period, growth, per-rep attainment ranked, per-product growth, concentration (top 20% share), and flagged anomalies (z-score > 2 on period-over-period change, zero-sales rows, attainment > 150% or < 50%).

If no script can run, do the same steps by hand and say which numbers are computed and which are estimated.

## 2. The analysis sequence (always in this order)

1. **Headline**: total actual vs target for the period, attainment %, growth vs prior period and vs same period last year if available.
2. **Shape of attainment**: % of reps ≥ 100%, median attainment, spread (P10–P90). A team at 98% with half the reps below 80% is a different problem from a team at 98% with everyone between 90 and 105.
3. **Where the gap is**: rank territories/reps by absolute gap to target, not by %. Three territories usually explain most of a miss.
4. **Product mix**: which products grew, which declined, and whether growth came from the focus products or from the tail.
5. **Concentration and risk**: share of sales from top 20% of accounts or reps; any single dependency above 25% gets a flag.
6. **Anomalies**: sudden spikes (possible period-end loading), zero months, attainment above 150% (quota or data problem), identical numbers across periods (stale data).
7. **Trend**: three-period moving direction for total and for the bottom quartile.

## 3. Output format

**Title line**: `<Region/Team> — <Period> sales review`

**Headline (3 lines max)**: attainment, growth, one-line cause.

**What drove it** (4–6 bullets, each with a number and a name — rep, territory or product).

**Watch list**: reps/territories below 80% for two consecutive periods, or dropping more than 15 points; anomalies with the likely explanation and what to verify.

**Three actions for the next period**, each with an owner and a date, e.g. "RBM North to review the 4 Delhi-2 accounts with zero orders (by 10 Oct)". Actions must be things a manager can actually do in 30 days.

**Appendix**: rep table (attainment, gap, rank, change vs prior), product table.

Length: the manager should read the non-appendix part in two minutes. Under 350 words before the appendix.

## 4. Language rules

- Numbers first, adjectives never: "North at 84% (−9 pts vs Aug), gap ₹6.2L, of which Delhi-2 ₹3.1L", not "North had a challenging month".
- Say "miss", "gap", "declined" — not "softness", "headwinds", "opportunity".
- One decimal at most for percentages; round money to the unit the team uses (₹L, ₹Cr, $K).
- Do not praise or blame people; describe results and name the next action.
- If the data cannot support a claim, say "cannot tell from this file" and name the column that would be needed.
