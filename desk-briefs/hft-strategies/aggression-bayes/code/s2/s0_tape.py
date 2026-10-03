"""S2 data audit (S0-T) for S2-LXT-1S. PAPER ONLY.

On one develop day (spec section 2.3): checks that raw `trades` reconcile with the 1 m klines in every
minute, and compares sweep groups built from `trades` with the program's aggTrades definition.
Writes s0_tape.csv (check, known, recomputed, match). With --measure, prints the values without
comparing (used once to record the known answers in the spec).
"""
import argparse
import os
import sys
import zipfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import AGG_TPL, TRADES_TPL, agg_sweep_groups, fetch_verified, read_aggtrades, read_trades, sha256_file, sweep_groups  # noqa: E402

AUDIT_DAY = "2026-06-30"
KNOWN = {
    "trades_sha256": "042563f0f275523f9513060c5f73526706106ab60daa79bcec992e33492d35c6",
    "trades_has_header": True,
    "trade_rows": 4297703,
    "trade_id_gaps": 6088,
    "trade_id_max_step": 4,
    "time_decreasing_steps": 0,
    "day_volume_btc": "191646.301",
    "minutes_mismatch_volume": 0,
    "minutes_mismatch_taker_buy": 0,
    "minutes_mismatch_count": 0,
    "seconds_with_trades": 84201,
    "taker_groups": 890137,
    "sweep_groups_trades": 150006,
    "sweep_qty_btc_trades": "81726.879",
    "sweep_groups_nonmonotone": 513,
    "agg_rows": 1596010,
    "sweep_keys_trades": 149281,
    "sweep_keys_aggtrades": 141448,
    "aggtrades_sweep_keys_found_in_trades": 141448,
    "agg_ids_absent_from_trades": 697,
}


def milli(x):
    return np.rint(np.asarray(x, dtype=np.float64) * 1000).astype(np.int64)


def measure(data_dir, kline_dir, day):
    got = {}
    rt = fetch_verified(data_dir, "perp_trades", TRADES_TPL, day)
    ra = fetch_verified(data_dir, "perp_aggtrades", AGG_TPL, day)
    if rt["status"] != "OK" or ra["status"] != "OK":
        raise SystemExit(f"S0-T download/checksum failure: trades={rt['status']} aggTrades={ra['status']}")
    got["trades_sha256"] = sha256_file(rt["path"])
    t = read_trades(rt["path"])
    got["trades_has_header"] = bool(t["has_header"])
    got["trade_rows"] = int(len(t["id"]))
    steps = np.diff(t["id"])
    got["trade_id_gaps"] = int((steps != 1).sum())
    got["trade_id_max_step"] = int(steps.max())
    got["time_decreasing_steps"] = int((np.diff(t["time"]) < 0).sum())
    got["day_volume_btc"] = f"{t['qty_m'].sum() / 1000:.3f}"

    kpath = os.path.join(kline_dir, f"BTCUSDT-1m-{day}.zip")
    with zipfile.ZipFile(kpath) as z:
        with z.open(z.namelist()[0]) as f:
            k = pd.read_csv(f)
    m0 = k["open_time"].to_numpy(np.int64) // 60000
    m = t["time"] // 60000
    idx = m - m0[0]
    nb = len(m0)
    vol = np.bincount(idx, weights=t["qty_m"], minlength=nb).astype(np.int64)
    tbv = np.bincount(idx, weights=np.where(~t["ibm"], t["qty_m"], 0), minlength=nb).astype(np.int64)
    cnt = np.bincount(idx, minlength=nb)
    got["minutes_mismatch_volume"] = int((vol != milli(k["volume"])).sum())
    got["minutes_mismatch_taker_buy"] = int((tbv != milli(k["taker_buy_volume"])).sum())
    got["minutes_mismatch_count"] = int((cnt != k["count"].to_numpy(np.int64)).sum())
    got["seconds_with_trades"] = int(np.unique(t["time"] // 1000).size)

    g = sweep_groups(t)
    sw = g["n_px"] >= 2
    got["taker_groups"] = int(len(g["n_px"]))
    got["sweep_groups_trades"] = int(sw.sum())
    got["sweep_qty_btc_trades"] = f"{g['qty_m'][sw].sum() / 1000:.3f}"
    got["sweep_groups_nonmonotone"] = int((g["nonmono"] & sw).sum())

    a = read_aggtrades(ra["path"])
    got["agg_rows"] = int(len(a["agg_id"]))
    ag = agg_sweep_groups(a)
    asw = ag["n_px"] >= 2
    tkeys = set(zip(g["time"][sw].tolist(), g["ibm"][sw].tolist()))
    akeys = set(zip(ag["time"][asw].tolist(), ag["ibm"][asw].tolist()))
    got["sweep_keys_trades"] = int(len(tkeys))
    got["sweep_keys_aggtrades"] = int(len(akeys))
    got["aggtrades_sweep_keys_found_in_trades"] = int(len(tkeys & akeys))
    lo, hi = a["first_id"], a["last_id"]
    covered = np.unique(np.concatenate([np.arange(x, y + 1) for x, y in zip(lo, hi)]))
    got["agg_ids_absent_from_trades"] = int(np.setdiff1d(covered, t["id"]).size)
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--klines", required=True, help="directory holding BTCUSDT-1m-<date>.zip perp klines")
    ap.add_argument("--out")
    ap.add_argument("--measure", action="store_true")
    args = ap.parse_args()
    got = measure(args.data, args.klines, AUDIT_DAY)
    if args.measure:
        for k, v in got.items():
            print(f"{k}: {v}")
        return
    rows = [{"check": k, "known": KNOWN[k], "recomputed": got[k], "match": str(KNOWN[k]) == str(got[k])} for k in KNOWN]
    out = pd.DataFrame(rows)
    os.makedirs(args.out, exist_ok=True)
    out.to_csv(os.path.join(args.out, "s0_tape.csv"), index=False)
    print(out.to_string(index=False))
    if not out["match"].all():
        print("S0-T FAIL")
        sys.exit(1)
    print("S0-T PASS")


if __name__ == "__main__":
    main()
