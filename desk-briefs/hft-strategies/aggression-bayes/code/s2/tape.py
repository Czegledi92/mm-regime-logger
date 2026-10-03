"""S2 phase A: per-day raw trades -> QC, 1 s bars and per-event window features. PAPER ONLY.

  python tape.py fetch   --data D                      download + checksum every trades day (spec 2.1)
  python tape.py process --data D --klines K --work W  per day: reconcile (2.2), 1 s bars (4), features (5-6)

No trades file dated 2026-09-01 or later is ever requested (test T10).
A day that fails download, checksum, time order or kline reconciliation is logged and dropped as a slice.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import TRADES_TPL, fetch_verified, read_trades, sha256_file, sweep_groups  # noqa: E402

FIRST = dt.date(2025, 12, 12)
LAST = dt.date(2026, 8, 31)
TEST_START = dt.date(2026, 9, 1)
WINDOWS = ("M60", "B5", "B15", "B30", "B60")
TOUCH_BP = 5.0
TICK2 = 0.2 - 1e-9


def days():
    out, d = [], FIRST
    while d <= LAST:
        out.append(d.isoformat())
        d += dt.timedelta(days=1)
    assert all(dt.date.fromisoformat(x) < TEST_START for x in out)
    return out


def day_start_ms(day):
    return int(dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc).timestamp() * 1000)


def cmd_fetch(args):
    with ThreadPoolExecutor(args.workers) as ex:
        rows = list(ex.map(lambda d: fetch_verified(args.data, "perp_trades", TRADES_TPL, d), days()))
    with open(os.path.join(args.data, "trades_fetch_log.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    bad = [r for r in rows if r["status"] != "OK"]
    print(f"trades files: {len(rows)}  ok: {len(rows) - len(bad)}  failed: {len(bad)}")
    for r in bad:
        print("FAIL", r["date"], r["status"])


def milli(x):
    return np.rint(np.asarray(x, dtype=np.float64) * 1000).astype(np.int64)


def second_bars(t, d0):
    sec = (t["time"] - d0) // 1000
    n = np.bincount(sec, minlength=86400).astype(np.int32)
    v = np.bincount(sec, weights=t["qty_m"], minlength=86400).astype(np.int64)
    buy = np.bincount(sec, weights=np.where(~t["ibm"], t["qty_m"], 0), minlength=86400).astype(np.int64)
    out = {"n": n, "v_m": v, "buy_m": buy}

    def last_of(mask):
        idx = np.flatnonzero(mask)
        px = np.full(86400, np.nan)
        ms = np.full(86400, -1, np.int64)
        if idx.size:
            s = sec[idx]
            lst = idx[np.r_[s[1:] != s[:-1], True]]
            px[sec[lst]] = t["price"][lst]
            ms[sec[lst]] = t["time"][lst]
        return px, ms

    out["last_px"], out["last_ms"] = last_of(np.ones(len(sec), bool))
    out["last_buy_px"], out["last_buy_ms"] = last_of(~t["ibm"])
    out["last_sell_px"], out["last_sell_ms"] = last_of(t["ibm"])
    return pd.DataFrame(out)


def window_feats(t, sw_trade, gid, ia, ib, L, s, b):
    P, Q, I, T = t["price"][ia:ib], t["qty_m"][ia:ib], t["ibm"][ia:ib], t["time"][ia:ib]
    n = ib - ia
    out = {"T_d": b, "n": n, "v_m": int(Q.sum()), "buy_m": int(Q[~I].sum())}
    nan_keys = ("P_last", "cl", "pen", "at1_m", "at2_m", "sw_into_n", "sw_away_n", "sw_into_m", "sw_through",
                "v5_m", "buy5_m", "pen5_usdt", "back5_usdt")
    if n == 0:
        out.update({k: np.nan for k in nan_keys})
        return out
    rel = s * (P - L) / L * 1e4
    absbp = np.abs(P - L) / L * 1e4
    out["P_last"] = float(P[-1])
    out["cl"] = float(rel[-1])
    out["pen"] = float((-rel).max())
    out["at1_m"] = int(Q[absbp <= 1.0].sum())
    out["at2_m"] = int(Q[absbp <= 2.0].sum())
    into = I if s == 1 else ~I
    sw = sw_trade[ia:ib]
    G = gid[ia:ib]
    out["sw_into_n"] = int(np.unique(G[sw & into]).size)
    out["sw_away_n"] = int(np.unique(G[sw & ~into]).size)
    out["sw_into_m"] = int(Q[sw & into].sum())
    out["sw_through"] = int(bool(((rel < 0) & sw & into).any()))
    j = int(np.searchsorted(T, b - 5000, "left"))
    Q5, I5, P5 = Q[j:], I[j:], P[j:]
    out["v5_m"] = int(Q5.sum())
    out["buy5_m"] = int(Q5[~I5].sum())
    out["pen5_usdt"] = float((-s * (P5 - L)).max()) if P5.size else np.nan
    out["back5_usdt"] = float((s * (P5 - L)).max()) if P5.size else np.nan
    return out


def event_features(t, g, evd, kl):
    tm = t["time"]
    sw_trade = (g["n_px"] >= 2)[g["gid"]]
    kl_v = dict(zip(kl["open_time"].to_numpy(np.int64), milli(kl["volume"])))
    kl_b = dict(zip(kl["open_time"].to_numpy(np.int64), milli(kl["taker_buy_volume"])))
    rows = []
    for e in evd.itertuples(index=False):
        L, s, ot = float(e.L), int(e.s), int(e.open_time)
        i0 = int(np.searchsorted(tm, ot, "left"))
        i1 = int(np.searchsorted(tm, ot + 60000, "left"))
        x = s * (t["price"][i0:i1] - L) / L * 1e4
        hit = np.flatnonzero(x <= TOUCH_BP)
        row = {"event_id": int(e.event_id), "touch_ok": bool(hit.size > 0)}
        if hit.size == 0:
            rows.append(row)
            continue
        tau = int(tm[i0 + hit[0]])
        tau_s = tau // 1000
        row["tau_ms"] = tau
        row["tau_s"] = tau_s
        wins = {"M60": (ot, ot + 60000)}
        for w in (5, 15, 30, 60):
            wins[f"B{w}"] = (tau_s * 1000, (tau_s + w) * 1000)
        for name, (a, b) in wins.items():
            ia = int(np.searchsorted(tm, a, "left"))
            ib = int(np.searchsorted(tm, b, "left"))
            for k, v in window_feats(t, sw_trade, g["gid"], ia, ib, L, s, b).items():
                row[f"{name}_{k}"] = v
            row[f"{name}_a"] = a
        row["M60_kline_v_equal"] = bool(kl_v.get(ot, -1) == row["M60_v_m"])
        row["M60_kline_buy_equal"] = bool(kl_b.get(ot, -1) == row["M60_buy_m"])
        rows.append(row)
    return pd.DataFrame(rows)


_EPI = None


def _init(epi_path):
    global _EPI
    e = pd.read_parquet(epi_path)
    e = e[~e["placebo_dropped"] & e["eligible"]]
    _EPI = {d: grp[["event_id", "L", "s", "open_time"]] for d, grp in e.groupby("date")}


def process_day(day, data_dir, kline_dir, work):
    qc = {"date": day, "status": "", "rows": 0, "id_gaps": 0, "id_max_step": 0, "time_decreasing": 0, "outside_day": 0,
          "min_mismatch_volume": -1, "min_mismatch_taker_buy": -1, "min_mismatch_count": -1, "seconds_with_trades": 0,
          "sweeps": 0, "events": 0, "slice": ""}
    path = os.path.join(data_dir, "perp_trades", f"BTCUSDT-trades-{day}.zip")
    if not os.path.exists(path):
        qc.update(status="MISSING", slice="DROPPED")
        return qc
    t = read_trades(path)
    d0 = day_start_ms(day)
    steps = np.diff(t["id"])
    qc["rows"] = int(len(t["id"]))
    qc["id_gaps"] = int((steps != 1).sum())
    qc["id_max_step"] = int(steps.max()) if steps.size else 0
    qc["time_decreasing"] = int((np.diff(t["time"]) < 0).sum())
    qc["outside_day"] = int(((t["time"] < d0) | (t["time"] >= d0 + 86_400_000)).sum())
    with zipfile.ZipFile(os.path.join(kline_dir, f"BTCUSDT-1m-{day}.zip")) as z:
        with z.open(z.namelist()[0]) as f:
            kl = pd.read_csv(f)
    m0 = kl["open_time"].to_numpy(np.int64)
    if qc["time_decreasing"] or qc["outside_day"] or len(m0) != 1440 or m0[0] != d0:
        qc.update(status="TIME_ORDER_OR_RANGE", slice="DROPPED")
        return qc
    idx = (t["time"] - d0) // 60000
    vol = np.bincount(idx, weights=t["qty_m"], minlength=1440).astype(np.int64)
    tbv = np.bincount(idx, weights=np.where(~t["ibm"], t["qty_m"], 0), minlength=1440).astype(np.int64)
    cnt = np.bincount(idx, minlength=1440)
    qc["min_mismatch_volume"] = int((vol != milli(kl["volume"])).sum())
    qc["min_mismatch_taker_buy"] = int((tbv != milli(kl["taker_buy_volume"])).sum())
    qc["min_mismatch_count"] = int((cnt != kl["count"].to_numpy(np.int64)).sum())
    if qc["min_mismatch_volume"] or qc["min_mismatch_taker_buy"] or qc["min_mismatch_count"]:
        qc.update(status="KLINE_MISMATCH", slice="DROPPED")
        return qc
    sb = second_bars(t, d0)
    qc["seconds_with_trades"] = int((sb["n"] > 0).sum())
    os.makedirs(os.path.join(work, "sec"), exist_ok=True)
    sb.to_parquet(os.path.join(work, "sec", f"{day}.parquet"), index=False)
    g = sweep_groups(t)
    qc["sweeps"] = int((g["n_px"] >= 2).sum())
    evd = _EPI.get(day)
    if evd is not None and len(evd):
        fe = event_features(t, g, evd, kl)
        qc["events"] = int(len(fe))
        os.makedirs(os.path.join(work, "feat"), exist_ok=True)
        fe.to_parquet(os.path.join(work, "feat", f"{day}.parquet"), index=False)
    qc.update(status="OK", slice="KEPT")
    return qc


def cmd_process(args):
    flog = pd.read_csv(os.path.join(args.data, "trades_fetch_log.csv"), dtype=str)
    ok = dict(zip(flog["date"], flog["status"]))
    todo = days()
    rows = []
    run = [d for d in todo if ok.get(d) == "OK"]
    for d in todo:
        if ok.get(d) != "OK":
            rows.append({"date": d, "status": "FETCH:" + str(ok.get(d)), "slice": "DROPPED"})
    with ProcessPoolExecutor(args.workers, initializer=_init, initargs=(os.path.join(args.work, "episodes_s1.parquet"),)) as ex:
        futs = {d: ex.submit(process_day, d, args.data, args.klines, args.work) for d in run}
        for i, d in enumerate(run):
            rows.append(futs[d].result())
            if (i + 1) % 20 == 0:
                print(f"processed {i + 1}/{len(run)}", flush=True)
    qc = pd.DataFrame(rows).sort_values("date")
    meta = flog.set_index("date")[["url", "sha256", "expected", "status"]].rename(columns={"status": "fetch_status"})
    qc = qc.merge(meta, left_on="date", right_index=True, how="left")
    qc.to_csv(os.path.join(args.work, "tape_qc.csv"), index=False)
    print(qc["slice"].value_counts().to_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "process"])
    ap.add_argument("--data", required=True)
    ap.add_argument("--klines")
    ap.add_argument("--work")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    if args.cmd == "fetch":
        cmd_fetch(args)
    else:
        cmd_process(args)


if __name__ == "__main__":
    main()
