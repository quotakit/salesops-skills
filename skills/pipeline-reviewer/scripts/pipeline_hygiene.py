#!/usr/bin/env python3
"""Pipeline hygiene and forecast check for a CRM export (CSV/XLSX).

  python pipeline_hygiene.py export.csv --stage Stage --value Value --close "Expected close" --owner Owner
         [--created Created] [--activity "Last activity"] [--prob Probability] [--deal Deal]
         [--target 2500000] [--period-end 2026-12-31] [--today 2026-09-13] [--stale-days 30]
         [--won "Closed Won"] [--lost "Closed Lost"]
"""
import argparse, sys
import pandas as pd

DEFAULT_PROB = {"lead": .05, "qualified": .15, "discovery": .3, "proposal": .5, "negotiation": .75, "verbal": .9, "closed won": 1.0, "closed lost": 0.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file"); ap.add_argument("--stage", required=True); ap.add_argument("--value", required=True); ap.add_argument("--close", required=True)
    ap.add_argument("--owner", required=True); ap.add_argument("--deal"); ap.add_argument("--created"); ap.add_argument("--activity"); ap.add_argument("--prob")
    ap.add_argument("--target", type=float); ap.add_argument("--period-end"); ap.add_argument("--today"); ap.add_argument("--stale-days", type=int, default=30)
    ap.add_argument("--won", default="Closed Won"); ap.add_argument("--lost", default="Closed Lost")
    a = ap.parse_args()
    df = pd.read_csv(a.file) if a.file.lower().endswith(".csv") else pd.read_excel(a.file)
    today = pd.Timestamp(a.today) if a.today else pd.Timestamp.today().normalize()
    deal = a.deal or df.columns[0]
    df[a.value] = pd.to_numeric(df[a.value], errors="coerce").fillna(0)
    df[a.close] = pd.to_datetime(df[a.close], errors="coerce")
    if a.prob and a.prob in df.columns:
        p = pd.to_numeric(df[a.prob], errors="coerce")
        df["prob"] = (p / 100 if p.max() > 1 else p).fillna(0)
    else:
        df["prob"] = df[a.stage].astype(str).str.lower().map(lambda s: next((v for k, v in DEFAULT_PROB.items() if k in s), 0.3))
        print("Note: no probability column — using default stage probabilities; pass --prob to use the CRM's.")
    df["weighted"] = df[a.value] * df["prob"]
    st = df[a.stage].astype(str)
    df["open"] = ~st.str.lower().isin([a.won.lower(), a.lost.lower()])
    op = df[df.open].copy()
    won = df[st.str.lower() == a.won.lower()]; lost = df[st.str.lower() == a.lost.lower()]
    pe = pd.Timestamp(a.period_end) if a.period_end else None
    inp = op[op[a.close] <= pe] if pe is not None else op
    print("=== SUMMARY ===")
    print(f"Open deals {len(op)}  value {op[a.value].sum():,.0f}  weighted {op.weighted.sum():,.0f}")
    if len(won) + len(lost): print(f"Win rate (closed) {len(won)/(len(won)+len(lost)):.0%}  won value {won[a.value].sum():,.0f}")
    if pe is not None:
        print(f"Closing by {pe.date()}: {len(inp)} deals, value {inp[a.value].sum():,.0f}, weighted {inp.weighted.sum():,.0f}")
    if a.target:
        rem = a.target - won[a.value].sum()
        cov = inp[a.value].sum() / rem if rem > 0 else float("inf")
        print(f"Target {a.target:,.0f}  won so far {won[a.value].sum():,.0f}  remaining {rem:,.0f}  coverage {cov:.1f}x  weighted gap {rem - inp.weighted.sum():,.0f}")
        avg = won[a.value].mean() if len(won) else op[a.value].mean()
        wr = len(won) / (len(won) + len(lost)) if len(won) + len(lost) else 0.3
        need = max(0, (rem - inp.weighted.sum()) / (avg * wr)) if avg else 0
        print(f"Sourcing gap: ~{need:.0f} new opportunities at avg {avg:,.0f} and {wr:.0%} win rate")
    # flags
    flags = []
    slipped = op[op[a.close] < today]
    for _, r in slipped.iterrows(): flags.append((r[deal], r[a.owner], "slipped", f"close {r[a.close].date()} is past, still {r[a.stage]}", r[a.value]))
    if a.activity and a.activity in df.columns:
        op["last"] = pd.to_datetime(op[a.activity], errors="coerce")
        stale = op[(today - op["last"]).dt.days > a.stale_days]
        for _, r in stale.iterrows(): flags.append((r[deal], r[a.owner], "stale", f"no activity {(today - r['last']).days} days", r[a.value]))
    if a.created and a.created in df.columns:
        op["age"] = (today - pd.to_datetime(op[a.created], errors="coerce")).dt.days
        med = op.groupby(a.stage)["age"].median()
        old = op[op.apply(lambda r: r.age > 2 * med.get(r[a.stage], 0) and r.age > a.stale_days, axis=1)]
        for _, r in old.iterrows(): flags.append((r[deal], r[a.owner], "aging", f"{r.age} days old vs stage median {med.get(r[a.stage], 0):.0f}", r[a.value]))
        young_late = op[(op.age < 7) & (op.prob >= 0.75)]
        for _, r in young_late.iterrows(): flags.append((r[deal], r[a.owner], "skipped stages?", f"created {r.age} days ago, already {r[a.stage]}", r[a.value]))
    big = inp[inp.weighted > 0.3 * inp.weighted.sum()] if len(inp) else inp
    for _, r in big.iterrows(): flags.append((r[deal], r[a.owner], "concentration", f"{r.weighted / inp.weighted.sum():.0%} of weighted forecast", r[a.value]))
    print(f"\n=== FLAGS ({len(flags)}) ===")
    for f in sorted(flags, key=lambda x: -x[4])[:40]:
        print(f"{str(f[0])[:40]:40s} {str(f[1])[:14]:14s} {f[2]:16s} {f[3]}  ({f[4]:,.0f})")
    print("\n=== BY STAGE (open) ===")
    print(op.groupby(a.stage).agg(deals=(deal, "count"), value=(a.value, "sum"), weighted=("weighted", "sum")).round(0).to_string())
    print("\n=== BY OWNER (open) ===")
    g = op.groupby(a.owner).agg(deals=(deal, "count"), value=(a.value, "sum"), weighted=("weighted", "sum"))
    g["slipped"] = slipped.groupby(a.owner)[deal].count(); g = g.fillna(0)
    print(g.sort_values("weighted", ascending=False).round(0).to_string())
    if pe is not None:
        print("\n=== FORECAST BY MONTH (open, closing in period) ===")
        m = inp.groupby(inp[a.close].dt.to_period("M")).agg(deals=(deal, "count"), value=(a.value, "sum"), weighted=("weighted", "sum"))
        print(m.round(0).to_string())


if __name__ == "__main__":
    main()
