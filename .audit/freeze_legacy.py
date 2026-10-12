# S0-01: Freeze legacy experiment evidence (read-only audit)
# Records hashes of legacy script, JSON result, docs; re-computes headline stats
# from the stored JSON so old metrics are documented, not re-derived.
import hashlib, json, os, sys
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TZ = timezone(timedelta(hours=8))

TARGETS = [
    "scripts/backtest_focus_random5.py",
    "data/reviews/FOCUS_V1_BACKTEST_RANDOM5_20261011.json",
    "docs/backtest-evidence/random5-walkforward.md",
    "docs/integration/INTEGRATION_PLAN_20261012.md",
    "README.md",
]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

out = {
    "purpose": "S0-01 legacy evidence freeze: manifest of legacy backtest artifacts at commit 02154d7",
    "created_at": datetime.now(TZ).isoformat(),
    "git_commit": "02154d7327530f699be23017534d6157bd646f5a",
    "files": {},
}

for rel in TARGETS:
    p = os.path.join(ROOT, rel)
    st = os.stat(p)
    out["files"][rel] = {
        "sha256": sha256(p),
        "size_bytes": st.st_size,
        "mtime": datetime.fromtimestamp(st.st_mtime, TZ).isoformat(),
    }

# Recompute headline stats from stored JSON (documenting legacy metric definition)
# Actual schema: top-level list of per-stock summaries with strat_ret/bh_ret as decimals
jpath = os.path.join(ROOT, "data/reviews/FOCUS_V1_BACKTEST_RANDOM5_20261011.json")
data = json.load(open(jpath, encoding="utf-8"))
assert isinstance(data, list), "expected top-level list of per-stock summaries"

def num(x):
    try:
        return float(x)
    except Exception:
        return None

diffs, symbols, details = [], [], {}
n_trades_total = 0
for row in data:
    sym = row.get("sym") or "?"
    sr = num(row.get("strat_ret"))
    br = num(row.get("bh_ret"))
    n_trades_total += int(row.get("trades") or 0)
    if sr is None or br is None:
        details[sym] = {"note": "missing strat_ret/bh_ret, skipped"}
        continue
    diff_pp = (sr - br) * 100.0  # decimals -> percentage points
    symbols.append(sym)
    diffs.append(diff_pp)
    details[sym] = {
        "n_trades": int(row.get("trades") or 0),
        "winrate": row.get("winrate"),
        "avgR": row.get("avgR"),
        "sumR": row.get("sumR"),
        "strat_ret_pct": round(sr * 100.0, 4),
        "bh_ret_pct": round(br * 100.0, 4),
        "diff_pct_points": round(diff_pp, 4),
        "signal_counts": row.get("signals"),
    }

out["legacy_metric_recomputation"] = {
    "metric_definition": "per-stock (strat_ret - bh_ret)*100, then arithmetic mean across 5 stocks; documented as legacy definition (F09), NOT portfolio NAV alpha",
    "n_trades_total": n_trades_total,
    "n_symbols": len(symbols),
    "arithmetic_mean_diff_pct_points": round(sum(diffs) / len(diffs), 4) if diffs else None,
    "per_stock": details,
}

dest = os.path.join(ROOT, "docs", "audit")
os.makedirs(dest, exist_ok=True)
with open(os.path.join(dest, "legacy_freeze_manifest.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)
print(json.dumps({
    "files": {k: v["sha256"][:12] for k, v in out["files"].items()},
    "n_trades": out["legacy_metric_recomputation"]["n_trades_total"],
    "mean_diff": out["legacy_metric_recomputation"]["arithmetic_mean_diff_pct_points"],
}, ensure_ascii=False, indent=1))
