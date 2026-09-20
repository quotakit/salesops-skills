# Sales Ops Skills for Claude (free starter)

Two Claude skills that do the Monday-morning work of a sales-operations analyst, free and MIT-licensed:

| Skill | Ask Claude… | What it does |
|---|---|---|
| `sales-report-analyst` | "Summarise this month's sales export for the MBR" | Profiles your CSV/XLSX, computes attainment, gaps, leaders/laggards, anomalies and a trend, then writes the two-minute commentary with three actions. Script: `profile_sales.py`. |
| `pipeline-reviewer` | "Review this CRM export — what's stuck, what's real, what's my coverage?" | Coverage ratio, weighted forecast vs target, stale/slipped/aging deals, concentration risk, per-owner 1:1 questions. Script: `pipeline_hygiene.py`. |

## Install

**Claude Code**
```bash
git clone https://github.com/quotakit/salesops-skills.git
cp -r salesops-skills/skills/* ~/.claude/skills/        # or .claude/skills/ inside a project
```
Then just ask: *"Use sales-report-analyst on sales_aug.xlsx"*.

**Claude.ai / Cowork**: download the zip from Releases and upload it under Settings → Skills.

Scripts need Python 3.9+ and `pandas` (`pip install pandas openpyxl`). Run any script with `-h` for usage.

## Example

```
$ python skills/sales-report-analyst/scripts/profile_sales.py sales_aug.csv --analyse --product Product --territory Territory
=== HEADLINE — period 2026-08 ===
Actual 977,663  Target 950,000  Attainment 102.9%
Prior period 2026-07: 978,852  Growth -0.1%
Reps: 6  >=100%: 5 (83%)  median 103.5%  P10 98.3%  P90 107.7%
...
```

Claude then turns that into: headline, what drove it (with names and numbers), a watch list, and three actions with owners and dates.

## The full pack

The Pro Pack adds six more skills with scripts: **incentive-plan-designer** (payout curves + Base/Upside/Downside cost simulation), **commission-plan-auditor** (gaming loopholes and cost exposure), **territory-planner** (A/B/C tiering, workload balance, call plans), **quota-setter** (fair allocation with guardrails), **field-force-sizing** (workload build-up + sensitivity grid) and **sales-review-prep** (MBR/QBR slides, 1:1 questions, follow-up tracker).

→ **QuotaKit Sales Ops Skills — Pro Pack** (https://quotakit.gumroad.com/l/salesops). One-time purchase, free updates.

## Contributing

Issues and PRs welcome — especially sample exports from CRMs the scripts do not parse cleanly yet (column names differ everywhere). Please strip real customer data before sharing.

## Licence

MIT. Written with AI assistance by a sales-force-effectiveness practitioner. The skills are opinions about how to run sales operations well, not legal or HR advice.
