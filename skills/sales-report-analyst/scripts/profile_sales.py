#!/usr/bin/env python3
"""Profile and analyse a sales export (CSV/XLSX).

  python profile_sales.py sales.xlsx                       # profile + guess column roles
  python profile_sales.py sales.xlsx --rep Rep --period Month --target Target --actual Actual --analyse
Optional: --product Product --territory Territory --top 10
"""
import argparse, sys, re
try:
    import pandas as pd
except ImportError:
    sys.exit("pandas is required: pip install pandas openpyxl")

GUESS = {
    "rep": r"rep|employee|salesperson|owner|mr\b|name",
    "territory": r"territory|region|zone|area|hq|city",
    "product": r"product|brand|sku|item",
    "period": r"period|month|date|week|quarter",
    "target": r"target|quota|budget|plan",
    "actual": r"actual|sales|revenue|achieved|value|amount",
}


def load(path):
    return pd.read_csv(path) if path.lower().endswith(".csv") else pd.read_excel(path)


def guess_roles(df):
    roles = {}
    for role, pat in GUESS.items():
        for c in df.columns:
            if re.search(pat, str(c), re.I) and c not in roles.values():
                roles[role] = c; break
    return roles


def profile(df):
    print(f"Rows: {len(df):,}   Columns: {len(df.columns)}")
    for c in df.columns:
        s = df[c]
        print(f"  {c!s:28s} {str(s.dtype):10s} non-null {s.notna().sum():>7,}  unique {s.nunique():>6,}  e.g. {s.dropna().astype(str).iloc[0] if s.notna().any() else ''}")
    print("\nGuessed roles:", guess_roles(df))


def analyse(df, a):
    d = df.copy()
    d[a.actual] = pd.to_numeric(d[a.actual], errors="coerce").fillna(0)
    d[a.target] = pd.to_numeric(d[a.target], errors="coerce").fillna(0)
    periods = sorted(d[a.period].dropna().unique(), key=lambda x: pd.to_datetime(x, errors="coerce") if not isinstance(x, (int, float)) else x)
    if len(periods) < 1:
        sys.exit("No periods found")
    cur, prev = periods[-1], (periods[-2] if len(periods) > 1 else None)
    C = d[d[a.period] == cur]; P = d[d[a.period] == prev] if prev is not None else None
    ta, tt = C[a.actual].sum(), C[a.target].sum()
    print(f"\n=== HEADLINE — period {cur} ===")
    print(f"Actual {ta:,.0f}  Target {tt:,.0f}  Attainment {ta/tt:.1%}" if tt else f"Actual {ta:,.0f} (no target)")
    if P is not None:
        pa = P[a.actual].sum()
        print(f"Prior period {prev}: {pa:,.0f}  Growth {ta/pa-1:+.1%}" if pa else "Prior period had zero sales")
    # per rep
    g = C.groupby(a.rep).agg(actual=(a.actual, "sum"), target=(a.target, "sum"))
    g["attainment"] = g.apply(lambda r: r.actual / r.target if r.target else float("nan"), axis=1)
    g["gap"] = g.target - g.actual
    if P is not None:
        gp = P.groupby(a.rep).agg(p_actual=(a.actual, "sum"), p_target=(a.target, "sum"))
        gp["p_att"] = gp.apply(lambda r: r.p_actual / r.p_target if r.p_target else float("nan"), axis=1)
        g = g.join(gp[["p_att"]]); g["att_change_pts"] = (g.attainment - g.p_att) * 100
    g = g.sort_values("gap", ascending=False)
    att = g.attainment.dropna()
    print(f"\nReps: {len(g)}  >=100%: {(att>=1).sum()} ({(att>=1).mean():.0%})  median {att.median():.1%}  P10 {att.quantile(.1):.1%}  P90 {att.quantile(.9):.1%}")
    print(f"\n=== LARGEST GAPS TO TARGET (top {a.top}) ===")
    print(g.head(a.top).round(3).to_string())
    print(f"\n=== TOP PERFORMERS ===")
    print(g.sort_values("attainment", ascending=False).head(a.top).round(3).to_string())
    for dim in (a.territory, a.product):
        if dim and dim in d.columns:
            gd = C.groupby(dim)[a.actual].sum().sort_values(ascending=False)
            print(f"\n=== BY {dim.upper()} (period {cur}) ===")
            if P is not None:
                pd_ = P.groupby(dim)[a.actual].sum()
                tbl = pd.DataFrame({"actual": gd, "prior": pd_}).fillna(0)
                tbl["growth"] = tbl.apply(lambda r: r.actual / r.prior - 1 if r.prior else float("nan"), axis=1)
                print(tbl.sort_values("actual", ascending=False).round(3).to_string())
            else:
                print(gd.round(0).to_string())
            share = gd.sort_values(ascending=False)
            k = max(1, int(round(len(share) * 0.2)))
            print(f"Concentration: top 20% ({k}) = {share.head(k).sum()/share.sum():.0%} of sales" if share.sum() else "")
    # anomalies
    print("\n=== ANOMALIES ===")
    flags = []
    for rep, r in g.iterrows():
        if r.target and r.attainment > 1.5: flags.append(f"{rep}: attainment {r.attainment:.0%} — check quota or data")
        if r.target and r.attainment < 0.5: flags.append(f"{rep}: attainment {r.attainment:.0%} — below 50%")
        if r.actual == 0: flags.append(f"{rep}: zero sales this period")
    if P is not None and "att_change_pts" in g:
        ch = g.att_change_pts.dropna()
        if len(ch) > 3 and ch.std() > 0:
            z = (ch - ch.mean()) / ch.std()
            for rep, zz in z[abs(z) > 2].items():
                flags.append(f"{rep}: attainment moved {g.loc[rep,'att_change_pts']:+.0f} pts vs prior (z={zz:.1f})")
    print("\n".join(flags) if flags else "None flagged")
    # trend
    if len(periods) >= 3:
        tot = d.groupby(a.period)[a.actual].sum().reindex(periods)
        print("\n=== TREND (last periods) ===")
        print(tot.tail(6).round(0).to_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file"); ap.add_argument("--rep"); ap.add_argument("--period"); ap.add_argument("--target"); ap.add_argument("--actual")
    ap.add_argument("--product"); ap.add_argument("--territory"); ap.add_argument("--top", type=int, default=10); ap.add_argument("--analyse", action="store_true")
    a = ap.parse_args()
    df = load(a.file)
    if not a.analyse:
        profile(df); return
    roles = guess_roles(df)
    for k in ("rep", "period", "target", "actual"):
        if getattr(a, k) is None:
            setattr(a, k, roles.get(k))
        if getattr(a, k) is None or getattr(a, k) not in df.columns:
            sys.exit(f"Column for {k} not found; pass --{k}")
    analyse(df, a)


if __name__ == "__main__":
    main()
