"""Spec section 13 tests T1-T10 for S1-LXF-BAR v1.1. PAPER ONLY.

Usage: python tests_s1.py --data /tmp/s1data --s0 <dir holding s0_reconciliation.csv> --out <dir>
Writes tests_report.csv. Only the develop + validate stage is run here; no test-split statistic is computed.
"""
import argparse
import dataclasses
import datetime as dt
import hashlib
import os
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

import s1

FEATURES = ["L", "s", "d_t", "tsib_bucket", "speed15", "dist_vwap_sigma", "ib_width_rel", "vwap_slope30", "touch_seq",
            "TI_t", "TI_into", "pen_class", "cl_t", "vz_t", "atsz_t", "oi_d5c", "TI_spot_t", "clock_ok", "impulse",
            "placebo_dropped", "cluster_id", "Y_level", "Y_fwd_3", "Y_fwd_5", "Y_fwd_15", "Y_fwd_30"]
KEY = ["box", "g", "level_type", "kind", "offset"]


def frames_equal(a, b, cols):
    bad = []
    for c in cols:
        x, y = a[c].to_numpy(), b[c].to_numpy()
        if x.dtype.kind == "f" or y.dtype.kind == "f":
            same = np.isclose(x.astype(float), y.astype(float), rtol=0, atol=1e-9, equal_nan=True)
        else:
            same = x == y
        if not same.all():
            bad.append(f"{c}:{int((~same).sum())}")
    return bad


def t1(b1):
    D = dt.date(2026, 8, 14)
    cfg = s1.Cfg()
    sc = ["develop", "validate"]
    full = s1.run(b1, cfg, sc)
    trunc = s1.run(b1.truncate_after(D), cfg, sc)
    fe = full["events"][full["events"]["date"] <= D].sort_values(KEY).reset_index(drop=True)
    te = trunc["events"][trunc["events"]["date"] <= D].sort_values(KEY).reset_index(drop=True)
    if len(fe) != len(te) or not (fe[KEY].to_numpy() == te[KEY].to_numpy()).all():
        return False, f"event sets differ: full {len(fe)} vs truncated {len(te)}"
    complete = (te["Y_level"] != "NA") & te["Y_fwd_30"].notna()
    bad = frames_equal(fe[complete], te[complete], FEATURES)
    fg = full["gate"][full["gate"]["date"] <= D].sort_values(KEY).reset_index(drop=True)
    tg = trunc["gate"][trunc["gate"]["date"] <= D].sort_values(KEY).reset_index(drop=True)
    bad += frames_equal(fg, tg, ["H_L", "conf_HL", "veto_HL", "liq_veto_5m", "print_confirm", "edge_ok", "first_fail", "AGREE"])
    return not bad, f"events <= {D}: {len(fe)} ({int(complete.sum())} with complete labels); mismatches: {bad or 'none'}"


def t2():
    n = 6
    Hi = np.array([101.0, 103.0, 102.0, 105.0, 104.0, 103.0])
    Lo = np.array([99.0, 100.0, 100.0, 101.0, 102.0, 101.0])
    C = np.array([100.0, 102.0, 101.0, 104.0, 103.0, 102.0])
    O = np.array([100.0, 100.0, 102.0, 101.0, 104.0, 103.0])
    v = np.array([2.0, 1.0, 3.0, 5.0, 1.0, 1.0])
    z = np.zeros(n)
    bars = s1.Bars(1, [], O, Hi, Lo, C, v, z, z, np.ones(n, bool), z, z, np.zeros(1))
    b = {"g0": 0, "nb": n, "ib_n": 2, "ib_complete": True}
    lv = s1.box_levels(bars, b)
    tp = (Hi + Lo + C) / 3
    hand = (tp[0] * 2 + tp[1] * 1 + tp[2] * 3) / 6
    ok = np.isnan(lv["vwap"][0]) and np.isclose(lv["vwap"][1], tp[0]) and np.isclose(lv["vwap"][3], hand)
    bars2 = dataclasses.replace(bars, Hi=Hi.copy(), C=C.copy())
    bars2.Hi[3] = 500.0
    bars2.C[3] = 400.0
    lv2 = s1.box_levels(bars2, b)
    ok = ok and np.isclose(lv2["vwap"][3], hand) and not np.isclose(lv2["vwap"][4], lv["vwap"][4])
    return bool(ok), f"toy VWAP at bar 3 = {lv['vwap'][3]:.6f}, hand = {hand:.6f}; bar 3 change leaves VWAP(3) unchanged"


def t2_reset(b1):
    boxes = s1.build_boxes(b1)
    utc = [b for b in boxes if b["box"] == "UTC"][100:103] + [b for b in boxes if b["box"] == "NY"][50:53]
    for b in utc:
        lv = s1.box_levels(b1, b)
        g0 = b["g0"]
        tp0 = (b1.Hi[g0] + b1.Lo[g0] + b1.C[g0]) / 3
        if not (np.isnan(lv["vwap"][0]) and np.isclose(lv["vwap"][1], tp0)):
            return False, f"VWAP does not reset at anchor of {b['box']} {b['date']}"
    return True, "VWAP(anchor) undefined and VWAP(anchor+1) = TP(anchor) on 3 UTC and 3 NY boxes"


def t3():
    want = {dt.date(2026, 3, 6): (14, 30), dt.date(2026, 3, 9): (13, 30), dt.date(2025, 10, 31): (13, 30), dt.date(2025, 11, 3): (14, 30)}
    got = {d: (s1.ny_anchor_utc(d).hour, s1.ny_anchor_utc(d).minute) for d in want}
    return got == want, "; ".join(f"{d}: {h:02d}:{m:02d} UTC" for d, (h, m) in got.items())


def t4(b1, res):
    boxes = {b["box_id"]: b for b in res["boxes"]}
    ev = res["events"]
    bad = 0
    for bid, k in zip(ev["box_id"], ev["k"]):
        b = boxes[bid]
        if not (b["win_lo"] <= k < b["win_hi"]):
            bad += 1
    ny_dates = {b["date"] for b in res["boxes"] if b["box"] == "NY"}
    hol = sorted(ny_dates & s1.NY_HOLIDAYS)
    wkend = sorted(d for d in ny_dates if d.weekday() >= 5)
    ot = pd.to_datetime(ev["open_time"], unit="ms", utc=True)
    ny = ev["box"] == "NY"
    et = ot[ny].dt.tz_convert(s1.ET)
    mins = et.dt.hour * 60 + et.dt.minute
    ny_ok = bool(((mins >= 10 * 60 + 45) & (mins < 15 * 60 + 30)).all())
    utc_m = ot[~ny].dt.hour * 60 + ot[~ny].dt.minute
    utc_ok = bool(((utc_m >= 75) & (utc_m < 23 * 60 + 30)).all())
    ok = bad == 0 and not hol and not wkend and ny_ok and utc_ok
    return ok, f"{len(ev)} events; outside window: {bad}; NY boxes on holidays: {hol or 'none'}; on weekends: {wkend or 'none'}; NY ET clock 10:45-15:30: {ny_ok}; UTC 01:15-23:30: {utc_ok}"


def t5(b1, res):
    rng = np.random.default_rng(1)
    ev = res["events"][~res["events"]["is_placebo"]]
    sample = ev.sample(200, random_state=1)
    cfg = s1.Cfg()
    bad_f = bad_l = changed = 0
    for r in sample.itertuples():
        g = np.array([r.g])
        s = np.array([r.s])
        L = np.array([r.L])
        base = s1.compute_labels(g, s, L, b1, cfg)
        pert = dataclasses.replace(b1, O=b1.O.copy(), Hi=b1.Hi.copy(), Lo=b1.Lo.copy(), C=b1.C.copy())
        f = rng.uniform(0.9, 1.1, size=r.g + 1)
        for a in ("O", "Hi", "Lo", "C"):
            getattr(pert, a)[:r.g + 1] *= f
        p1 = s1.compute_labels(g, s, L, pert, cfg)
        for h in cfg.h_fwd:
            if not np.isclose(base[f"Y_fwd_{h}"][0], p1[f"Y_fwd_{h}"][0], equal_nan=True):
                bad_f += 1
        pert2 = dataclasses.replace(b1, O=b1.O.copy(), Hi=b1.Hi.copy(), Lo=b1.Lo.copy(), C=b1.C.copy())
        for a in ("O", "Hi", "Lo", "C"):
            getattr(pert2, a)[:r.g] *= f[:r.g]
        p2 = s1.compute_labels(g, s, L, pert2, cfg)
        if base["Y_level"][0] != p2["Y_level"][0]:
            bad_l += 1
        pert3 = dataclasses.replace(b1, C=b1.C.copy())
        pert3.C[r.g + 3] *= 1.01
        if not np.isclose(base["Y_fwd_3"][0], s1.compute_labels(g, s, L, pert3, cfg)["Y_fwd_3"][0]):
            changed += 1
    ok = bad_f == 0 and bad_l == 0 and changed == 200
    return ok, f"200 events: Y_fwd changed by bars <= t: {bad_f}; Y_level changed by bars < t: {bad_l}; control (C_t+3 moved) changed Y_fwd_3 in {changed}/200"


def t6(fmt, metrics_days):
    ok = fmt["spot_1m_us_files"] == 366 and fmt["perp_1m_header_files"] == 366 and fmt["perp_5m_header_files"] == 366
    full = int((metrics_days["stamps"] == 288).sum())
    gaps = int((metrics_days["stamps"] != 288).sum())
    ok = ok and full == 366 and int(metrics_days["off_grid"].sum()) == 0 and int(metrics_days["duplicates"].sum()) == 0
    return ok, f"{fmt}; metrics days with 288 sorted on-grid stamps: {full}/366; flagged gap days: {gaps}"


def t7(data):
    log = pd.read_csv(os.path.join(data, "fetch_log.csv"))
    bad = []
    for r in log.itertuples():
        p = os.path.join(data, r.dataset, os.path.basename(r.url))
        if r.status != "OK" or not os.path.exists(p) or hashlib.sha256(open(p, "rb").read()).hexdigest() != r.expected:
            bad.append(f"{r.dataset}/{r.date}")
    return not bad, f"{len(log)} files re-hashed against .CHECKSUM; mismatches: {bad or 'none'}"


def t8(s0dir):
    df = pd.read_csv(os.path.join(s0dir, "s0_reconciliation.csv"))
    return bool(df["match"].all()), f"{int(df['match'].sum())}/{len(df)} known answers reproduced"


def t9(b1, res):
    boxes = res["boxes"]
    lv = {b["box_id"]: s1.box_levels(b1, b) for b in boxes}
    starts = np.array([b["g0"] for b in boxes])
    ev = res["events"]
    kept = ev[ev["is_placebo"] & ~ev["placebo_dropped"]]
    worst = np.inf
    for g, L in zip(kept["g"].to_numpy(), kept["L"].to_numpy()):
        vals = []
        for i in np.flatnonzero(starts <= g):
            b = boxes[i]
            k = g - b["g0"]
            if k >= b["nb"]:
                continue
            x = lv[b["box_id"]]
            vals.append(x["vwap"][k])
            if k >= b["ib_n"]:
                vals += [x["IBH"], x["IBL"], x["IBM"]]
        vals = np.array([v for v in vals if np.isfinite(v)])
        if vals.size:
            worst = min(worst, float(np.min(np.abs(vals - L) / L * 1e4)))
    return worst > 10, f"{len(kept)} kept placebo events; closest real level {worst:.4f} bp (must be > 10)"


def t10(data, here):
    hashes = []
    with tempfile.TemporaryDirectory() as d:
        for run in ("a", "b"):
            out = os.path.join(d, run)
            subprocess.run([sys.executable, os.path.join(here, "s1.py"), "--data", data, "--out", out, "--stage", "validate"],
                           check=True, capture_output=True)
            hashes.append({f: hashlib.sha256(open(os.path.join(out, f), "rb").read()).hexdigest() for f in sorted(os.listdir(out))})
    diff = [f for f in hashes[0] if hashes[0][f] != hashes[1].get(f)]
    return not diff and hashes[0].keys() == hashes[1].keys(), f"{len(hashes[0])} output files compared byte for byte; differing: {diff or 'none'}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--s0", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    b1, b5, man, metrics_days, fmt = s1.load_all(args.data)
    res = s1.run(b1, s1.Cfg(), ["develop", "validate"])
    rows = []
    for name, fn in (
        ("T1 Prefix invariance", lambda: t1(b1)),
        ("T2 VWAP (toy box)", t2),
        ("T2 VWAP (reset at anchor)", lambda: t2_reset(b1)),
        ("T3 DST", t3),
        ("T4 Windows", lambda: t4(b1, res)),
        ("T5 Labels", lambda: t5(b1, res)),
        ("T6 Formats", lambda: t6(fmt, metrics_days)),
        ("T7 Checksums", lambda: t7(args.data)),
        ("T8 S0", lambda: t8(args.s0)),
        ("T9 Placebo hygiene", lambda: t9(b1, res)),
        ("T10 Determinism", lambda: t10(args.data, here)),
    ):
        ok, detail = fn()
        rows.append({"test": name, "pass": bool(ok), "detail": detail})
        print(("PASS " if ok else "FAIL ") + name + ": " + detail, flush=True)
    os.makedirs(args.out, exist_ok=True)
    pd.DataFrame(rows).to_csv(os.path.join(args.out, "tests_report.csv"), index=False)
    if not all(r["pass"] for r in rows):
        sys.exit(1)


if __name__ == "__main__":
    main()
