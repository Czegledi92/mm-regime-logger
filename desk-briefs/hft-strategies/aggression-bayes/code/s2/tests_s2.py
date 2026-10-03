"""Spec section 14 tests T1-T10 for S2-LXT-1S v1.0. PAPER ONLY.

Usage: python tests_s2.py --data /tmp/s2data --klines /tmp/s1data/perp_1m --work /tmp/s2work --results <results/s2>
Reads the outputs of episodes.py, tape.py and s2.py; writes tests_report.csv and s0_tape.csv into --results.
Develop and validate only: no trades file dated 2026-09-01 or later is opened.
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import s2  # noqa: E402
import tape  # noqa: E402
from common import read_trades, sweep_groups  # noqa: E402

T3_DAY = "2026-06-30"
TEST_START = "2026-09-01"
FEAT_KEYS = ("n", "v_m", "buy_m", "P_last", "cl", "pen", "at1_m", "at2_m", "sw_into_n", "sw_away_n", "sw_into_m", "sw_through",
             "v5_m", "buy5_m", "pen5_usdt", "back5_usdt")


def _same(x, y, tol=0.0):
    x, y = float(x), float(y)
    if np.isnan(x) or np.isnan(y):
        return np.isnan(x) and np.isnan(y)
    return abs(x - y) <= tol


def scored_events(work):
    ep = pd.read_parquet(os.path.join(work, "episodes_s1.parquet"))
    ep = ep[~ep["placebo_dropped"] & ep["eligible"]]
    fe = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(os.path.join(work, "feat", "*.parquet")))], ignore_index=True)
    return ep.merge(fe, on="event_id", how="left")


def t1(ev):
    ok = ev["touch_ok"].fillna(False).astype(bool)
    return bool(ok.all()), f"{len(ev)} develop and validate events; with a touching trade in the touch bar: {int(ok.sum())}"


def t2(ev):
    v, buy = ev["M60_v_m"].to_numpy(float), ev["M60_buy_m"].to_numpy(float)
    kl_eq = bool(ev["M60_kline_v_equal"].all() and ev["M60_kline_buy_equal"].all())
    ti = (2 * buy - v) / v
    d_ti = np.nanmax(np.abs(ti - ev["TI_t"].to_numpy(float)))
    d_pen = np.nanmax(np.abs(ev["M60_pen"].to_numpy(float) - ev["pen_t"].to_numpy(float)))
    d_cl = np.nanmax(np.abs(ev["M60_cl"].to_numpy(float) - ev["cl_t"].to_numpy(float)))
    nan_mismatch = int((np.isnan(ti) != ev["TI_t"].isna().to_numpy()).sum())
    ok = kl_eq and d_ti <= 1e-9 and d_pen <= 1e-9 and d_cl <= 1e-9 and nan_mismatch == 0
    return ok, (f"{len(ev)} events; minute volume and taker-buy volume equal the klines in integer thousandths: {kl_eq}; "
                f"max |TI_w - TI_t| {d_ti:.3g}, |pen_w - pen_t| {d_pen:.3g}, |cl_w - cl_t| {d_cl:.3g}; NaN mismatches {nan_mismatch}")


def _window(t, a, b, L, s):
    g = sweep_groups(t)
    sw = (g["n_px"] >= 2)[g["gid"]]
    ia = int(np.searchsorted(t["time"], a, "left"))
    ib = int(np.searchsorted(t["time"], b, "left"))
    return tape.window_feats(t, sw, g["gid"], ia, ib, L, s, b)


def _sec_days(work, day, before, after):
    d = dt.date.fromisoformat(day)
    out = []
    for k in range(-before, after + 1):
        out.append(pd.read_parquet(os.path.join(work, "sec", f"{d + dt.timedelta(days=k)}.parquet")))
    return out


def t3(data, work, results, ev):
    day = T3_DAY
    t = read_trades(os.path.join(data, "perp_trades", f"BTCUSDT-trades-{day}.zip"))
    tm = t["time"]
    d0 = tape.day_start_ms(day)
    e = ev[ev["date"] == day].sort_values("event_id")
    res = pd.read_parquet(os.path.join(results, "episodes.parquet")).set_index("event_id")
    rng = np.random.default_rng(20261003)
    rows = {}

    # features: perturb every trade at or after T_d (price through the level, size, aggressor side)
    n_cmp = n_bad = n_store_bad = 0
    for r in e.itertuples(index=False):
        L, s = float(r.L), int(r.s)
        for c in tape.WINDOWS:
            a, b = int(getattr(r, f"{c}_a")), int(getattr(r, f"{c}_T_d"))
            lo, hi = int(np.searchsorted(tm, a - 2000, "left")), int(np.searchsorted(tm, b + 30000, "left"))
            sl = {k: t[k][lo:hi] for k in ("id", "price", "qty_m", "time", "ibm")}
            base = _window(sl, a, b, L, s)
            m = sl["time"] >= b
            pert = dict(sl)
            pert["price"] = np.where(m, sl["price"] - s * 50.0, sl["price"])
            pert["qty_m"] = np.where(m, sl["qty_m"] * 3 + 7, sl["qty_m"])
            pert["ibm"] = np.where(m, ~sl["ibm"], sl["ibm"])
            got = _window(pert, a, b, L, s)
            for k in FEAT_KEYS:
                n_cmp += 1
                n_bad += not _same(base[k], got[k])
                n_store_bad += not _same(base[k], getattr(r, f"{c}_{k}"), 1e-12)

    # second-bar features: burst threshold (seconds before W) and same-hour z (20 prior days)
    sec2 = s2.seconds_from_bars(_sec_days(work, day, 1, 0), d0 // 1000 - 86400)
    sec21 = s2.seconds_from_bars(_sec_days(work, day, 20, 0), d0 // 1000 - 20 * 86400)
    p_cmp = p_bad = z_cmp = z_bad = z_store_bad = 0
    for c, w in (("M60", 60), ("B15", 15)):
        starts = (e[f"{c}_a"].to_numpy(np.int64) // 1000) - (d0 // 1000 - 86400)
        base = s2.burst_p95(sec2, starts, w)
        for i, k0 in enumerate(starts):
            pert = dict(sec2)
            pert["v"] = sec2["v"].copy()
            pert["buy"] = sec2["buy"].copy()
            pert["v"][k0:] = rng.integers(0, 10**6, len(pert["v"]) - k0)
            pert["buy"][k0:] = pert["v"][k0:] // 3
            got = s2.burst_p95(pert, np.array([k0]), w)[0]
            p_cmp += 1
            p_bad += not _same(base[i], got)
        blocks = s2.hour_blocks(sec21, w)
        pb = {k: v.copy() for k, v in blocks.items()}
        for k in pb:
            pb[k][20:] = rng.normal(size=pb[k][20:].shape)
        hh = ((e[f"{c}_a"].to_numpy(np.int64) - d0) // 3_600_000).astype(int)
        lv = np.log(e[f"{c}_v_m"].to_numpy(float))
        for i, eid in enumerate(e["event_id"].to_numpy()):
            zb = s2.robust_z(blocks["v"], 20, hh[i], lv[i], {}, "v")
            zp = s2.robust_z(pb["v"], 20, hh[i], lv[i], {}, "v")
            z_cmp += 1
            z_bad += not _same(zb, zp)
            z_store_bad += not _same(zb, res.at[eid, f"{c}_vz_w"], 1e-9)
    oi_stamp_ok = True
    for c in tape.WINDOWS:
        Td = ev[f"{c}_T_d"].to_numpy(np.int64)
        kk = (Td - s2.s1.T0_MS) // s2.s1.OI_STEP_MS
        oi_stamp_ok &= bool((s2.s1.T0_MS + kk * s2.s1.OI_STEP_MS <= Td).all())
    feat_ok = n_bad == 0 and n_store_bad == 0 and p_bad == 0 and z_bad == 0 and z_store_bad == 0 and oi_stamp_ok
    rows["T3a No look-ahead: features"] = (feat_ok, (
        f"{day}, {len(e)} events x 5 clocks: {n_cmp} trade-window values compared after perturbing every trade at or after T_d, "
        f"changed {n_bad}; recomputed vs stored {n_store_bad} differ. Burst threshold after perturbing seconds >= window start: "
        f"{p_bad}/{p_cmp} changed. Same-hour vz after perturbing the event day's blocks: {z_bad}/{z_cmp} changed; vs stored "
        f"{z_store_bad} differ. OI stamp <= T_d for every event and clock: {oi_stamp_ok}"))

    # labels: rebuild the mid proxy from perturbed trades of the day (next day unchanged) with the s2 code
    nxt = _sec_days(work, day, 0, 1)[1]
    k0 = d0 // 1000

    def labs(tt, kd, s, L):
        sec = s2.seconds_from_bars([tape.second_bars(tt, d0), nxt], k0)
        return s2.labels(sec["mid"], kd, s, L, 1, level=True)

    def same_lab(x, y):
        return all(_same(x[h][0], y[h][0]) for h in s2.HORIZONS) and x["level"][0] == y["level"][0]

    base_sec = tape.second_bars(t, d0)
    stored_sec = pd.read_parquet(os.path.join(work, "sec", f"{day}.parquet"))
    sec_equal = bool(base_sec.equals(stored_sec))
    base_mid = s2.seconds_from_bars([base_sec, nxt], k0)["mid"]
    cnt = {"literal": 0, "bounded": 0, "control": 0, "store_bad": 0, "n": 0}
    for r in e.itertuples(index=False):
        L, s = np.array([float(r.L)]), np.array([float(r.s)])
        for c in ("B15", "M60"):
            Td = int(getattr(r, f"{c}_T_d"))
            kd = np.array([Td // 1000 - k0])
            base = s2.labels(base_mid, kd, s, L, 1, level=True)
            cnt["n"] += 1
            stored = res.loc[r.event_id]
            cnt["store_bad"] += not (all(_same(base[h][0], stored[f"{c}_Y1s_{h}"], 1e-9) for h in s2.HORIZONS)
                                     and base["level"][0] == stored[f"{c}_Y1s_level"])
            for nm, m in (("literal", tm < Td), ("bounded", tm < Td - 60_000), ("control", tm >= Td + 1000)):
                pt = dict(t)
                pt["price"] = np.where(m, t["price"] * 1.002, t["price"])
                pt["qty_m"] = np.where(m, t["qty_m"] * 2 + 1, t["qty_m"])
                cnt[nm] += not same_lab(base, labs(pt, kd, s, L))
    rows["T3b Labels vs trades before the entry second (spec wording)"] = (cnt["literal"] == 0, (
        f"{cnt['n']} event-clock labels (B15, M60); changed after perturbing every trade before T_d: {cnt['literal']}. "
        "Section 4 lets the entry mid proxy reuse the last buy and sell prints up to 10 s old (last price up to 60 s)"))
    rows["T3c Labels vs trades more than 60 s before T_d (beyond the section 4 lookback)"] = (
        cnt["bounded"] == 0 and cnt["store_bad"] == 0 and sec_equal,
        f"changed {cnt['bounded']}/{cnt['n']}; recomputed labels vs stored differ: {cnt['store_bad']}; second bars equal stored: {sec_equal}")
    rows["T3d Control: perturbing trades after the entry second"] = (
        cnt["control"] > 0, f"labels changed in {cnt['control']}/{cnt['n']} (must be > 0)")
    return rows


def t4(data, klines, results):
    p = subprocess.run([sys.executable, os.path.join(HERE, "s0_tape.py"), "--data", data, "--klines", klines, "--out", results],
                       capture_output=True, text=True)
    s0 = pd.read_csv(os.path.join(results, "s0_tape.csv"))
    return p.returncode == 0 and bool(s0["match"].all()), f"{int(s0['match'].sum())}/{len(s0)} known answers reproduced"


def t5(data, work):
    log = pd.read_csv(os.path.join(data, "trades_fetch_log.csv"), dtype=str)
    qc = pd.read_csv(os.path.join(work, "tape_qc.csv"), dtype=str)
    kept = set(qc.loc[qc["slice"] == "KEPT", "date"])

    def h(day):
        x = hashlib.sha256()
        with open(os.path.join(data, "perp_trades", f"BTCUSDT-trades-{day}.zip"), "rb") as f:
            for chunk in iter(lambda: f.read(1 << 22), b""):
                x.update(chunk)
        return day, x.hexdigest()

    exp = dict(zip(log["date"], log["expected"]))
    with ThreadPoolExecutor(8) as ex:
        got = dict(ex.map(h, sorted(kept)))
    bad = [d for d in got if got[d] != exp.get(d)]
    failed = log[log["status"] != "OK"]
    dropped_ok = set(failed["date"]).isdisjoint(kept)
    return not bad and dropped_ok, (f"{len(got)} kept trades files re-hashed against .CHECKSUM; mismatches: {bad or 'none'}; "
                                    f"fetch failures: {len(failed)} (all dropped: {dropped_ok})")


def t6(work, ev):
    qc = pd.read_csv(os.path.join(work, "tape_qc.csv"), dtype={"date": str})
    k = qc[qc["slice"] == "KEPT"]
    mm = int(k[["min_mismatch_volume", "min_mismatch_taker_buy", "min_mismatch_count"]].to_numpy().sum())
    days_used = set(ev["date"])
    unkept = sorted(days_used - set(k["date"]))
    return mm == 0 and not unkept, f"{len(k)} kept days; mismatching minutes on kept days: {mm}; event days not kept: {unkept or 'none'}"


def t7(work, results):
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, os.path.join(HERE, "s2.py"), "--work", work, "--out", tmp], check=True, capture_output=True)
        names = sorted(f for f in os.listdir(tmp))
        diff = []
        for f in names:
            with open(os.path.join(tmp, f), "rb") as x, open(os.path.join(results, f), "rb") as y:
                if x.read() != y.read():
                    diff.append(f)
    return not diff, f"{len(names)} s2.py output files compared byte for byte with a second run; differing: {diff or 'none'}"


def t8(work):
    with open(os.path.join(work, "t8.json")) as f:
        x = json.load(f)
    return bool(x["pass"]), x["detail"] + " (S1 independent check, develop and validate)"


def t9(work):
    with open(os.path.join(work, "t9.json")) as f:
        x = json.load(f)
    ok = x["same_event_ids"] and x["lean_cells_equal"] and all(v for k, v in x.items() if k.startswith("equal_"))
    cols = ", ".join(k[6:] for k in x if k.startswith("equal_"))
    return bool(ok), f"{x['n_rows']} rebuilt rows equal results/s1_v1.1/events.parquet on event_id, {cols}; lean cells equal: {x['lean_cells_equal']}"


def t10(data, work, results):
    log = pd.read_csv(os.path.join(data, "trades_fetch_log.csv"), dtype=str)
    files = [os.path.basename(p)[15:25] for p in glob.glob(os.path.join(data, "perp_trades", "*.zip"))]
    qc = pd.read_csv(os.path.join(work, "tape_qc.csv"), dtype=str)
    late = sorted({d for d in list(log["date"]) + files + list(qc["date"]) if d >= TEST_START})
    ep = pd.read_parquet(os.path.join(work, "episodes_s1.parquet"))
    out_ep = pd.read_parquet(os.path.join(results, "episodes.parquet"))
    gl = pd.read_parquet(os.path.join(results, "gate_log.parquet"))
    splits = set(ep["split"]) | set(out_ep["split"]) | set(gl["split"])
    max_date = max(out_ep["date"].max(), gl["date"].max())
    ok = not late and splits <= {"develop", "validate"} and max_date < TEST_START
    return ok, (f"trades dates requested {log['date'].min()} to {log['date'].max()} ({len(log)} files); dated {TEST_START} or later: "
                f"{late or 'none'}; splits in frames: {sorted(splits)}; latest event date {max_date}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--klines", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--results", required=True)
    args = ap.parse_args()
    ev = scored_events(args.work)
    rows = []
    for name, fn in (("T1 Touch trade", lambda: t1(ev)), ("T2 Minute equals S1", lambda: t2(ev))):
        rows.append((name,) + fn())
    for name, (ok, det) in t3(args.data, args.work, args.results, ev).items():
        rows.append((name, ok, det))
    for name, fn in (("T4 S0-T", lambda: t4(args.data, args.klines, args.results)), ("T5 Checksums", lambda: t5(args.data, args.work)),
                     ("T6 Reconciliation", lambda: t6(args.work, ev)), ("T7 Determinism", lambda: t7(args.work, args.results)),
                     ("T8 Placebo hygiene", lambda: t8(args.work)), ("T9 S1 episodes", lambda: t9(args.work)),
                     ("T10 No test split", lambda: t10(args.data, args.work, args.results))):
        rows.append((name,) + fn())
        print(rows[-1], flush=True)
    rep = pd.DataFrame(rows, columns=["test", "pass", "detail"])
    rep.to_csv(os.path.join(args.results, "tests_report.csv"), index=False)
    pd.set_option("display.max_colwidth", 400)
    print(rep.to_string(index=False))


if __name__ == "__main__":
    main()
