"""S0 reconciliation for S1-LXF-BAR v1.1 (spec section 2.2). PAPER ONLY.

Recomputes the 2026-10-01 known answers from the downloaded files and writes
s0_reconciliation.csv with columns: check, known, recomputed, match.
Exit code 1 if any check fails (spec test T8).

Quantities are compared as integer thousandths of a BTC (the exchange quantity step is 0.001),
so "equal" means exactly equal.
"""
import argparse
import hashlib
import os
import sys
import zipfile

import numpy as np
import pandas as pd

KNOWN = {
    "perp_1m_sha256": "062f32fefdfb1d1cfbb6d58ee04c28dd6c45dbf2b52ed60fa4ad6a27b0b19bc5",
    "trades_minutes_mismatch_volume": 0,
    "trades_minutes_mismatch_taker_buy": 0,
    "trades_minutes_mismatch_count": 0,
    "day_volume_btc": "143164.950",
    "trade_rows": 3249979,
    "sum_kline_count": 3249979,
    "agg_day_volume_equal": True,
    "agg_day_taker_buy_equal": True,
    "agg_minutes_mismatch_volume": 139,
    "agg_max_volume_gap_btc": "3.863",
    "agg_minutes_mismatch_taker_buy": 90,
    "agg_minutes_mismatch_open": 49,
    "agg_ids_absent_from_trades": 730,
}


def read_csv_zip(path, **kw):
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:
            return pd.read_csv(f, **kw)


def milli(x):
    return np.rint(np.asarray(x, dtype=np.float64) * 1000).astype(np.int64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    d = "2026-10-01"
    kpath = os.path.join(args.data, "perp_1m", f"BTCUSDT-1m-{d}.zip")
    tpath = os.path.join(args.data, "perp_trades", f"BTCUSDT-trades-{d}.zip")
    apath = os.path.join(args.data, "perp_aggtrades", f"BTCUSDT-aggTrades-{d}.zip")

    got = {}
    got["perp_1m_sha256"] = hashlib.sha256(open(kpath, "rb").read()).hexdigest()

    k = read_csv_zip(kpath)
    assert str(k.columns[0]) == "open_time", "perp klines must carry a header row"
    k["m"] = (k["open_time"] // 60000).astype(np.int64)
    k = k.set_index("m").sort_index()
    k_vol = pd.Series(milli(k["volume"]), index=k.index)
    k_tbv = pd.Series(milli(k["taker_buy_volume"]), index=k.index)
    k_cnt = k["count"].astype(np.int64)

    t = read_csv_zip(tpath, dtype={"is_buyer_maker": str})
    t["m"] = t["time"] // 60000
    t["q"] = milli(t["qty"])
    t["buy"] = t["is_buyer_maker"].str.lower() == "false"
    g = t.groupby("m")
    t_vol = g["q"].sum().reindex(k.index, fill_value=0)
    t_tbv = t[t["buy"]].groupby("m")["q"].sum().reindex(k.index, fill_value=0)
    t_cnt = g.size().reindex(k.index, fill_value=0)
    got["trades_minutes_mismatch_volume"] = int((t_vol != k_vol).sum())
    got["trades_minutes_mismatch_taker_buy"] = int((t_tbv != k_tbv).sum())
    got["trades_minutes_mismatch_count"] = int((t_cnt != k_cnt).sum())
    got["day_volume_btc"] = f"{t['q'].sum() / 1000:.3f}"
    got["trade_rows"] = int(len(t))
    got["sum_kline_count"] = int(k_cnt.sum())

    a = read_csv_zip(apath, dtype={"is_buyer_maker": str}).sort_values("agg_trade_id")
    a["m"] = a["transact_time"] // 60000
    a["q"] = milli(a["quantity"])
    a["buy"] = a["is_buyer_maker"].str.lower() == "false"
    ga = a.groupby("m")
    a_vol = ga["q"].sum().reindex(k.index, fill_value=0)
    a_tbv = a[a["buy"]].groupby("m")["q"].sum().reindex(k.index, fill_value=0)
    a_open = ga["price"].first().reindex(k.index)
    got["agg_day_volume_equal"] = bool(a["q"].sum() == k_vol.sum())
    got["agg_day_taker_buy_equal"] = bool(a.loc[a["buy"], "q"].sum() == k_tbv.sum())
    vol_gap = (a_vol - k_vol).abs()
    got["agg_minutes_mismatch_volume"] = int((vol_gap != 0).sum())
    got["agg_max_volume_gap_btc"] = f"{vol_gap.max() / 1000:.3f}"
    got["agg_minutes_mismatch_taker_buy"] = int((a_tbv != k_tbv).sum())
    got["agg_minutes_mismatch_open"] = int((~np.isclose(a_open.values, k["open"].values, rtol=0, atol=1e-9)).sum())
    lo = a["first_trade_id"].to_numpy(np.int64)
    hi = a["last_trade_id"].to_numpy(np.int64)
    span = np.concatenate([np.arange(x, y + 1) for x, y in zip(lo, hi)])
    covered = np.unique(span)
    got["agg_ids_absent_from_trades"] = int(np.setdiff1d(covered, t["id"].to_numpy(np.int64), assume_unique=False).size)

    rows = []
    for key, known in KNOWN.items():
        rec = got[key]
        rows.append({"check": key, "known": known, "recomputed": rec, "match": str(known) == str(rec)})
    out = pd.DataFrame(rows)
    os.makedirs(args.out, exist_ok=True)
    out.to_csv(os.path.join(args.out, "s0_reconciliation.csv"), index=False)
    print(out.to_string(index=False))
    if not out["match"].all():
        print("S0 FAIL")
        sys.exit(1)
    print("S0 PASS")


if __name__ == "__main__":
    main()
