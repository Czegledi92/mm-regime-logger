"""S2-LXT-1S v1.0 phase B: labels, 1 s rules, gate and statistics. PAPER ONLY.

Implements 20261003-s2-level-x-tape-1s-spec.md. Section numbers refer to that spec.
Reads the outputs of episodes.py and tape.py from --work. Develop and validate only (section 0, D4):
the analysis asserts that no test-split event enters any frame.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "s1"))
sys.path.insert(0, HERE)
import s1  # noqa: E402
from tape import FIRST, days  # noqa: E402

SCORED = ["develop", "validate"]
DAYS = days()
K0 = int(dt.datetime(FIRST.year, FIRST.month, FIRST.day, tzinfo=dt.timezone.utc).timestamp())
HORIZONS = (30, 60, 180, 300, 900)
H_PRIMARY = 180
LEVEL_H = 1800
WLEN = {"M60": 60, "B5": 5, "B15": 15, "B30": 30, "B60": 60}
FEES = s1.FEES
PRIMARY_FEE = s1.PRIMARY_FEE
TI_THR = 0.20
CATS = ["level_type", "box", "s", "tsib_bucket", "hour_utc", "dow"]
LEVEL_NUMS = ["speed15", "dist_vwap_sigma", "ib_width_rel", "vwap_slope30", "touch_seq"]
TAPE_NUMS = ["log_sweep_into_n", "log_sweep_away_n", "sweep_into_share", "sweep_through", "at_level_share", "absorb",
             "burst_into", "nz_w", "ti_last5_into"]


# ----------------------------------------------------------------------------- seconds (section 4)


def _ffill(px, ms, cpx, cms):
    idx = np.where(ms >= 0, np.arange(len(ms)), -1)
    idx = np.maximum.accumulate(idx)
    has = idx >= 0
    j = np.clip(idx, 0, None)
    return np.where(has, px[j], cpx), np.where(has, ms[j], cms)


def build_seconds(work, kept):
    bars = [pd.read_parquet(os.path.join(work, "sec", f"{d}.parquet")) if d in kept else None for d in DAYS]
    return seconds_from_bars(bars, K0)


def seconds_from_bars(bars, k0):
    """bars: one second-bar frame per consecutive UTC day starting at epoch second k0 (None for a dropped day)."""
    ns = len(bars) * 86400
    v = np.zeros(ns, np.int64)
    buy = np.zeros(ns, np.int64)
    n = np.zeros(ns, np.int32)
    ok = np.zeros(ns, bool)
    mid = np.full(ns, np.nan)
    last = np.full(ns, np.nan)
    carry = {k: (np.nan, -1) for k in ("last", "buy", "sell")}
    for di, sb in enumerate(bars):
        sl = slice(di * 86400, (di + 1) * 86400)
        if sb is None:
            carry = {k: (np.nan, -1) for k in carry}
            continue
        v[sl], buy[sl], n[sl], ok[sl] = sb["v_m"].to_numpy(), sb["buy_m"].to_numpy(), sb["n"].to_numpy(), True
        lp, lm = _ffill(sb["last_px"].to_numpy(), sb["last_ms"].to_numpy(), *carry["last"])
        bp, bm = _ffill(sb["last_buy_px"].to_numpy(), sb["last_buy_ms"].to_numpy(), *carry["buy"])
        sp, sm = _ffill(sb["last_sell_px"].to_numpy(), sb["last_sell_ms"].to_numpy(), *carry["sell"])
        end_ms = (k0 + di * 86400 + np.arange(86400) + 1).astype(np.int64) * 1000
        last_ok = (lm >= 0) & (end_ms - lm <= 60_000)
        both = (bm >= 0) & (end_ms - bm <= 10_000) & (sm >= 0) & (end_ms - sm <= 10_000) & (bp >= sp)
        mid[sl] = np.where(last_ok, np.where(both, (bp + sp) / 2, lp), np.nan)
        last[sl] = np.where(last_ok, lp, np.nan)
        carry = {"last": (lp[-1], lm[-1]), "buy": (bp[-1], bm[-1]), "sell": (sp[-1], sm[-1])}
    return {"v": v, "buy": buy, "n": n, "ok": ok, "mid": mid, "last": last}


# ----------------------------------------------------------------------------- trailing distributions (section 6)


def hour_blocks(sec, w):
    nd = len(sec["v"]) // 86400
    nb = 3600 // w
    out = {}
    with np.errstate(divide="ignore", invalid="ignore"):
        V = sec["v"].reshape(nd, 24, nb, w).sum(-1).astype(float)
        N = sec["n"].reshape(nd, 24, nb, w).sum(-1).astype(float)
        okd = sec["ok"].reshape(nd, 86400).all(1)
        out["v"] = np.where(V > 0, np.log(V), np.nan)
        out["n"] = np.where(N > 0, np.log(N), np.nan)
        out["ats"] = np.where((V > 0) & (N > 0), np.log(V / N), np.nan)
    for k in out:
        out[k][~okd] = np.nan
    return out


def robust_z(blocks, di, h, x, cache, key):
    ck = (key, di, h)
    if ck not in cache:
        if di < 20:
            cache[ck] = (np.nan, np.nan)
        else:
            vals = blocks[di - 20:di, h, :].ravel()
            vals = vals[np.isfinite(vals)]
            if vals.size < 2:
                cache[ck] = (np.nan, np.nan)
            else:
                med = np.median(vals)
                mad = np.median(np.abs(vals - med))
                cache[ck] = (med, mad) if mad > 0 else (np.nan, np.nan)
    med, mad = cache[ck]
    return (x - med) / (1.4826 * mad)


def burst_p95(sec, starts, w):
    """95th percentile of the rolling w-second |sum signed qty| over the 86,400 s before each window start."""
    sg = (2 * sec["buy"] - sec["v"]).astype(float)
    C = np.concatenate([[0.0], np.cumsum(sg)])
    okc = np.concatenate([[0], np.cumsum(~sec["ok"])])
    out = np.full(len(starts), np.nan)
    for i, k0 in enumerate(starts):
        lo = k0 - 86400
        if lo < 0:
            continue
        ks = np.arange(lo, k0 - w + 1)
        R = np.abs(C[ks + w] - C[ks])
        good = (okc[ks + w] - okc[ks]) == 0
        if good.sum() > 0:
            out[i] = np.percentile(R[good], 95)
    return out


# ----------------------------------------------------------------------------- labels (section 8)


def labels(px, kd, s, L, latency=1, level=False):
    """kd: decision second index (T_d / 1000 - K0). Entry = px at kd - 1 + latency (end of second T_d/1000 for latency 1)."""
    ns = len(px)
    ke = kd - 1 + latency
    out = {}
    valid = (ke >= 0) & (ke < ns)
    ent = np.where(valid, px[np.clip(ke, 0, ns - 1)], np.nan)
    for h in HORIZONS:
        kx = ke + h
        ex = np.where(kx < ns, px[np.clip(kx, 0, ns - 1)], np.nan)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[h] = s * np.log(ex / ent) * 1e4
    if level:
        lab = np.full(len(kd), "NA", dtype=object)
        for i in range(len(kd)):
            if not np.isfinite(ent[i]):
                continue
            a, b = ke[i], min(ke[i] + LEVEL_H + 1, ns)
            path = s[i] * (px[a:b] - L[i]) / L[i] * 1e4
            up = np.flatnonzero(path >= 10.0)
            dn = np.flatnonzero(path <= -10.0)
            fu = up[0] if up.size else np.inf
            fd = dn[0] if dn.size else np.inf
            first = min(fu, fd)
            stop = int(first) if np.isfinite(first) else len(path)
            if np.isnan(path[:stop]).any():
                continue
            if np.isfinite(first):
                lab[i] = "RESPECT" if fu < fd else "BREAK"
            elif ke[i] + LEVEL_H < ns:
                lab[i] = "NONE"
        out["level"] = lab
    return out


# ----------------------------------------------------------------------------- features per clock (sections 6-7)


def clock_frame(ep, c, sec, blocks, zcache, oi, p95):
    ok = ep["tape_ok"].to_numpy(bool)
    s = ep["s"].to_numpy()
    v = ep[f"{c}_v_m"].to_numpy(float)
    buy = ep[f"{c}_buy_m"].to_numpy(float)
    n = ep[f"{c}_n"].to_numpy(float)
    a = ep[f"{c}_a"].fillna(0).to_numpy(np.int64)
    Td = ep[f"{c}_T_d"].fillna(0).to_numpy(np.int64)
    day_end = (a // 86_400_000 + 1) * 86_400_000
    assert (Td[ok] <= day_end[ok]).all(), f"{c}: a window crosses midnight into another trades file"
    f = pd.DataFrame(index=ep.index)
    with np.errstate(invalid="ignore", divide="ignore"):
        ti = (2 * buy - v) / v
        f["TI_w"] = ti
        f["TI_into_w"] = -s * ti
        f["cl_w"] = ep[f"{c}_cl"].to_numpy(float)
        f["pen_w"] = ep[f"{c}_pen"].to_numpy(float)
        ka = a // 1000 - K0
        di, hh = ka // 86400, (ka % 86400) // 3600
        lv, ln_, la = np.log(v), np.log(n), np.log(v / n)
        w = WLEN[c]
        f["vz_w"] = [robust_z(blocks[w]["v"], d, h, x, zcache, ("v", w)) for d, h, x in zip(di, hh, lv)]
        f["nz_w"] = [robust_z(blocks[w]["n"], d, h, x, zcache, ("n", w)) for d, h, x in zip(di, hh, ln_)]
        f["atsz_w"] = [robust_z(blocks[w]["ats"], d, h, x, zcache, ("ats", w)) for d, h, x in zip(di, hh, la)]
        f["at_level_share"] = ep[f"{c}_at1_m"].to_numpy(float) / v
        f["at1_m"] = ep[f"{c}_at1_m"].to_numpy(float)
        f["at2_m"] = ep[f"{c}_at2_m"].to_numpy(float)
        f["sweep_into_n"] = ep[f"{c}_sw_into_n"].to_numpy(float)
        f["sweep_away_n"] = ep[f"{c}_sw_away_n"].to_numpy(float)
        f["log_sweep_into_n"] = np.log1p(f["sweep_into_n"])
        f["log_sweep_away_n"] = np.log1p(f["sweep_away_n"])
        f["sweep_into_share"] = ep[f"{c}_sw_into_m"].to_numpy(float) / v
        f["sweep_through"] = ep[f"{c}_sw_through"].to_numpy(float)
        v5, b5 = ep[f"{c}_v5_m"].to_numpy(float), ep[f"{c}_buy5_m"].to_numpy(float)
        f["ti_last5_into"] = -s * (2 * b5 - v5) / v5
        f["absorb"] = ((f["TI_into_w"] >= 0.6) & (f["vz_w"] >= 1) & (f["pen_w"] <= 1.0) & (f["cl_w"] >= 0)).astype(float)
        signed = np.abs(2 * buy - v)
        burst = (signed >= p95) & (np.abs(ti) >= 0.6)
        f["burst_into"] = np.where(burst, np.sign(f["TI_into_w"]), 0.0)
        f["sbr_raw_RESPECT"] = (f["ti_last5_into"] >= 0.20) & (ep[f"{c}_pen5_usdt"].to_numpy(float) >= 0.2 - 1e-9)
        f["sbr_raw_BREAK"] = (f["ti_last5_into"] <= -0.20) & (ep[f"{c}_back5_usdt"].to_numpy(float) >= 0.2 - 1e-9)
        kk = (Td - s1.T0_MS) // s1.OI_STEP_MS
        okk = (kk >= 1) & (kk < len(oi))
        kc = np.clip(kk, 1, len(oi) - 1)
        f["oi_d5c_w"] = np.where(okk, oi[kc] - oi[kc - 1], np.nan)
        f["oi_sign_w"] = np.nan_to_num(np.sign(f["oi_d5c_w"]), nan=0.0)
    num = [k for k in f.columns if f[k].dtype.kind == "f"]
    f.loc[~ok, num] = np.nan
    f["kd"] = np.where(ok, Td // 1000 - K0, -10**9)
    return f


def apply_rule(f, rule, ti_thr=TI_THR, at_col="at1_m"):
    r = pd.DataFrame(index=f.index)
    agg = f["TI_into_w"] >= ti_thr
    if rule == "1s":
        r["confirm_RESPECT"] = agg & (f["cl_w"] >= 0) & (f["vz_w"] >= 0) & (f["sweep_through"] == 0)
        r["confirm_BREAK"] = agg & (f["cl_w"] < 0) & (f["vz_w"] >= 0) & (f["sweep_into_n"] >= 1)
        r["veto_RESPECT"] = agg & (f["cl_w"] < -5)
        r["veto_BREAK"] = f["absorb"] == 1
        r["print_ok"] = (f[at_col] > 0) | (f["sweep_through"] == 1)
        r["absorb_veto"] = f["absorb"] == 1
        r["sbr_RESPECT"] = f["sbr_raw_RESPECT"]
        r["sbr_BREAK"] = f["sbr_raw_BREAK"]
    else:
        r["confirm_RESPECT"] = agg & (f["cl_w"] >= 0) & (f["vz_w"] >= 0)
        r["confirm_BREAK"] = agg & (f["cl_w"] < 0) & (f["vz_w"] >= 0)
        r["veto_RESPECT"] = agg & (f["cl_w"] < -5)
        r["veto_BREAK"] = agg & (f["cl_w"] >= 0)
        r["print_ok"] = f["vz_w"] >= 0
        r["absorb_veto"] = False
        r["sbr_RESPECT"] = False
        r["sbr_BREAK"] = False
    r["liq_veto_5m"] = (f["oi_d5c_w"] < 0) & (f["TI_w"].abs() >= 0.20)
    return r


# ----------------------------------------------------------------------------- gate (section 9)


def run_gate(e, lean, edge_cells, use_edge):
    e = e.sort_values("event_id").copy()
    keys = s1.cell_key(e)
    e["H_L"] = [lean.get(k, "NONE") for k in keys]
    e["cell"] = ["|".join(map(str, k)) for k in keys]
    HL = e["H_L"].to_numpy()
    pick = lambda a, b: np.where(HL == "RESPECT", e[a], np.where(HL == "BREAK", e[b], False)).astype(bool)  # noqa: E731
    e["conf_HL"] = pick("confirm_RESPECT", "confirm_BREAK")
    e["veto_HL"] = pick("veto_RESPECT", "veto_BREAK")
    e["sbr_HL"] = pick("sbr_RESPECT", "sbr_BREAK")
    e["absorb_HL"] = np.where(HL == "BREAK", e["absorb_veto"], False).astype(bool)
    e["depth_agree"] = "NT"
    e["edge_table_ok"] = [c in edge_cells for c in e["cell"]] if use_edge else True
    e["gate_event"] = True
    e["cluster_conflict"] = False
    for cid, grp in e[e["cluster_id"] >= 0].groupby("cluster_id"):
        order = sorted(grp.index, key=lambda i: (not e.at[i, "clock_ok"], e.at[i, "H_L"] == "NONE",
                                                  s1.TYPE_PRIORITY[e.at[i, "level_type"]], e.at[i, "box"] != "UTC"))
        hyp = {(e.at[i, "H_L"], e.at[i, "s"]) for i in grp.index if e.at[i, "clock_ok"] and e.at[i, "H_L"] != "NONE"}
        e.loc[grp.index, "gate_event"] = False
        e.at[order[0], "gate_event"] = True
        e.at[order[0], "cluster_conflict"] = len(hyp) > 1
    member_inst = e.groupby("cluster_id")["instance_id"].apply(list).to_dict()
    spent, reason = set(), []
    for i in e.index:
        r = e.loc[i]
        if not r["gate_event"]:
            reason.append("CLUSTER_DUP")
            continue
        if not r["clock_ok"]:
            reason.append("CLOCK_OK:" + ("CAL" if r["cal_blocked"] and r["impulse"] == "" else "IMPULSE_" + r["impulse"]))
            continue
        sub = ""
        if r["H_L"] == "NONE":
            sub = "NO_LEAN"
        elif r["cluster_conflict"]:
            sub = "CLUSTER_CONFLICT"
        elif not r["conf_HL"]:
            sub = "NO_CONFIRM"
        elif r["veto_HL"]:
            sub = "VETO"
        elif r["liq_veto_5m"]:
            sub = "LIQ_VETO"
        elif r["instance_id"] in spent:
            sub = "EPISODE_ONCE"
        if sub:
            reason.append("INDEPENDENT_AGREE:" + sub)
            continue
        if not r["print_ok"]:
            reason.append("PRINT_CONFIRM")
            continue
        if r["absorb_HL"]:
            reason.append("PRINT_CONFIRM:ABSORB_VETO")
            continue
        if use_edge and r["sbr_HL"]:
            reason.append("EDGE_OK:SIDE_RUN")
            continue
        if not r["edge_table_ok"]:
            reason.append("EDGE_OK")
            continue
        reason.append("AGREE")
        spent.add(r["instance_id"])
        if r["cluster_id"] >= 0:
            spent.update(member_inst.get(r["cluster_id"], []))
    e["first_fail"] = reason
    e["AGREE"] = e["first_fail"] == "AGREE"
    return e


def add_net(g, h):
    sign = np.where(g["H_L"] == "RESPECT", 1.0, np.where(g["H_L"] == "BREAK", -1.0, np.nan))
    y = sign * g[f"Y_fwd_{h}"].to_numpy()
    g["Y_dir"] = y
    for fee in FEES:
        g[f"Y_net_{fee:.2f}"] = y - fee
    g["fee_primary"] = np.where(g["H_L"] == "BREAK", PRIMARY_FEE["BREAK"], PRIMARY_FEE["RESPECT"])
    g["Y_net_primary"] = y - g["fee_primary"]
    return g


def edge_table(g_pre):
    rows = []
    d = g_pre[(g_pre["split"] == "develop") & (g_pre["H_L"] != "NONE")]
    for cell, grp in d.groupby("cell"):
        cand = grp[grp["first_fail"] == "AGREE"]
        pt, b = s1.boot_mean("develop", cand["date"].tolist(), cand["Y_net_primary"].to_numpy())
        lo, hi = s1.pct(b, 2.5, 97.5) if len(cand) else (np.nan, np.nan)
        rows.append({"cell": cell, "H_L": grp["H_L"].iloc[0], "n_candidates": int(np.isfinite(cand["Y_net_primary"]).sum()),
                     "mean_ynet": pt, "lo95": lo, "hi95": hi, "edge_ok": bool(np.isfinite(lo) and lo > 0)})
    return pd.DataFrame(rows, columns=["cell", "H_L", "n_candidates", "mean_ynet", "lo95", "hi95", "edge_ok"])


def full_gate(real, lean, h):
    g_pre = add_net(run_gate(real, lean, set(), use_edge=False), h)
    et = edge_table(g_pre)
    cells = set(et.loc[et["edge_ok"], "cell"])
    gate = add_net(run_gate(real, lean, cells, use_edge=True), h)
    return gate, et, g_pre


def g_stats(gate, g_pre):
    rows = []
    for sp in SCORED:
        gs = gate[(gate["split"] == sp) & gate["gate_event"]]
        groups = (("AGREE", gs[gs["AGREE"]]),
                  ("lean_FLAT_WATCH", gs[gs["clock_ok"] & (gs["H_L"] != "NONE") & (~gs["AGREE"])]),
                  ("pre_EDGE_candidates", g_pre[(g_pre["split"] == sp) & (g_pre["first_fail"] == "AGREE")]))
        for nm, e in groups:
            y = e["Y_net_primary"].to_numpy()
            pt, b = s1.boot_mean(sp, e["date"].tolist(), y)
            lo, hi = s1.pct(b, 2.5, 97.5)
            row = {"split": sp, "group": nm, "n": int(np.isfinite(y).sum()), "mean_ynet_primary": pt, "lo95": lo, "hi95": hi,
                   "n_RESPECT": int((e["H_L"] == "RESPECT").sum()), "n_BREAK": int((e["H_L"] == "BREAK").sum())}
            for fee in FEES:
                row[f"mean_fee_{fee:.2f}"] = float(np.nanmean(e[f"Y_net_{fee:.2f}"])) if len(e) else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def g_verdict(gate, gs):
    v = gs[(gs["split"] == "validate") & (gs["group"] == "AGREE")].iloc[0]
    pool = gate[(gate["split"] == "validate") & gate["AGREE"]]
    y = pool["Y_net_primary"]
    tot = y.sum()
    hshare = np.nan
    if len(pool) and tot > 0:
        ts = pd.to_datetime(pool["open_time"], unit="ms", utc=True)
        hshare = float(y.groupby(ts.dt.hour.to_numpy()).sum().max() / tot)
    conds = {"n_validate_ge_30": bool(v["n"] >= 30), "validate_mean_gt_0": bool(v["mean_ynet_primary"] > 0),
             "validate_lo95_gt_0": bool(v["lo95"] > 0), "hour_concentration_ok": bool(len(pool) > 0 and tot > 0 and hshare <= 0.5)}
    return {"VALIDATE_PASS": all(conds.values()), **conds, "max_hour_share": hshare, "month_rule": "deferred to an S2 test split"}


def h2_rows(real, plac, h):
    out = []
    for sp in SCORED:
        out += s1.h2_split(real[real["clock_ok"]], plac[plac["clock_ok"]], sp, h)
    return pd.DataFrame(out)


def h2_verdict(h2):
    ok = {}
    for H in ("RESPECT", "BREAK"):
        v = h2[(h2["H"] == H) & (h2["split"] == "validate")].iloc[0]
        ok[H] = bool(v["I_lo975"] > 0 and v["delta_real"] > 0)
    return {"VALIDATE_PASS": any(ok.values()), "validate_pass_RESPECT": ok["RESPECT"], "validate_pass_BREAK": ok["BREAK"]}


# ----------------------------------------------------------------------------- lift (S2-L)


def _design(x, ref, nums):
    X = pd.get_dummies(x[CATS].astype(str), drop_first=False)
    cols = pd.get_dummies(ref[CATS].astype(str), drop_first=False).columns
    X = X.reindex(columns=cols, fill_value=0).astype(float)
    xr = ref[nums].replace([np.inf, -np.inf], np.nan)
    xx = x[nums].replace([np.inf, -np.inf], np.nan)
    med = xr.median()
    mu, sd = xr.fillna(med).mean(), xr.fillna(med).std().replace(0, 1).fillna(1)
    Z = (xx.fillna(med) - mu) / sd
    return np.hstack([X.to_numpy(), Z.fillna(0).to_numpy()])


def _fit_ll(dev, val, nums, ycol):
    from sklearn.linear_model import LogisticRegression
    yd = (dev[ycol] == "RESPECT").to_numpy(int)
    yv = (val[ycol] == "RESPECT").to_numpy(int)
    m = LogisticRegression(C=1.0, max_iter=20000)
    m.fit(_design(dev, dev, nums), yd)
    p = np.clip(m.predict_proba(_design(val, dev, nums))[:, 1], 1e-9, 1 - 1e-9)
    ll = -(yv * np.log(p) + (1 - yv) * np.log(1 - p))
    br = (p - yv) ** 2
    return ll, br


def lift(frame, base_nums, tape_nums, ycol):
    d = frame[frame["clock_ok"] & frame[ycol].isin(["RESPECT", "BREAK"])]
    dev, val = d[d["split"] == "develop"], d[d["split"] == "validate"]
    ll1, br1 = _fit_ll(dev, val, base_nums, ycol)
    ll2, br2 = _fit_ll(dev, val, base_nums + tape_nums, ycol)
    W = s1.boot_W("validate")
    nd = W.shape[1]
    di = s1.day_index(val["date"].tolist(), "validate")
    res = {"n_develop": int(len(dev)), "n_validate": int(len(val)),
           "respect_share_validate": float((val[ycol] == "RESPECT").mean()) if len(val) else np.nan,
           "logloss_M1": float(ll1.mean()), "logloss_M2": float(ll2.mean()),
           "brier_M1": float(br1.mean()), "brier_M2": float(br2.mean())}
    boots = {}
    for nm, dlt in (("dLL", ll1 - ll2), ("dBrier", br1 - br2)):
        S, N = s1.sums(di, dlt, nd)
        with np.errstate(invalid="ignore", divide="ignore"):
            b = (W @ S) / (W @ N)
        res[nm] = float(S.sum() / N.sum())
        res[f"{nm}_lo95"], res[f"{nm}_hi95"] = s1.pct(b, 2.5, 97.5)
        boots[nm] = b
    return res, boots


# ----------------------------------------------------------------------------- assembly


def load(work):
    qc = pd.read_csv(os.path.join(work, "tape_qc.csv"))
    kept = set(qc.loc[qc["slice"] == "KEPT", "date"])
    ep = pd.read_parquet(os.path.join(work, "episodes_s1.parquet"))
    assert set(ep["split"]) <= set(SCORED), "test-split event in episodes"
    feats = []
    for d in sorted(kept):
        p = os.path.join(work, "feat", f"{d}.parquet")
        if os.path.exists(p):
            feats.append(pd.read_parquet(p))
    fe = pd.concat(feats, ignore_index=True)
    ep = ep.merge(fe, on="event_id", how="left")
    ep["tape_ok"] = ep["date"].isin(kept) & (ep["touch_ok"] == True)  # noqa: E712
    ep["date"] = [dt.date.fromisoformat(x) for x in ep["date"]]
    return ep, qc, kept


def frames(ep, f, r, lab, h, plac_kind="pct", clusters="include"):
    base = ep[["event_id", "kind", "is_placebo", "placebo_dropped", "eligible", "split", "date", "open_time", "L", "s", "level_type",
               "box", "tsib_bucket", "cluster_id", "instance_id", "clock_ok", "impulse", "cal_blocked", "tape_ok"]]
    x = pd.concat([base, f, r], axis=1)
    for hh, y in lab.items():
        if hh != "level":
            x[f"Y_fwd_{hh}"] = y
    use = x["tape_ok"] & x["eligible"]
    real = x[use & (x["kind"] == "real")]
    if clusters == "exclude":
        real = real[real["cluster_id"] < 0]
    plac = x[use & (x["kind"] == plac_kind) & ~x["placebo_dropped"]]
    return real.copy(), plac.copy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    ep, qc, kept = load(args.work)
    sec = build_seconds(args.work, kept)
    oi = np.load(os.path.join(args.work, "oi.npy"))
    cells = pd.read_csv(os.path.join(args.work, "s1_cells.csv"))
    lean = {(r.level_type, r.box, int(r.s), r.tsib_bucket): r.H_L for r in cells.itertuples() if r.lean}
    blocks = {w: hour_blocks(sec, w) for w in (5, 15, 30, 60)}
    zcache = {}
    ok = ep["tape_ok"].to_numpy()
    s_arr, L_arr = ep["s"].to_numpy(float), ep["L"].to_numpy(float)

    F, LAB = {}, {}
    for c in ("M60", "B5", "B15", "B30", "B60"):
        starts = np.where(ok, ep[f"{c}_a"].fillna(0).to_numpy(np.int64) // 1000 - K0, -1)
        p95 = np.full(len(ep), np.nan)
        if c in ("M60", "B15"):
            sel = np.flatnonzero(ok)
            p95[sel] = burst_p95(sec, starts[sel], WLEN[c])
        F[c] = clock_frame(ep, c, sec, blocks, zcache, oi, p95)
        kd = np.where(ok, F[c]["kd"].to_numpy(), -10**9)
        LAB[(c, "mid", 1)] = labels(sec["mid"], kd, s_arr, L_arr, 1, level=c in ("M60", "B15"))
        print("clock done:", c, flush=True)
    kd15 = np.where(ok, F["B15"]["kd"].to_numpy(), -10**9)
    LAB[("B15", "last", 1)] = labels(sec["last"], kd15, s_arr, L_arr, 1)
    LAB[("B15", "mid", 0)] = labels(sec["mid"], kd15, s_arr, L_arr, 0)
    with np.errstate(invalid="ignore"):
        gap = np.abs(sec["mid"] - sec["last"]) / sec["last"] * 1e4
    mid_gap_median_bp = float(np.nanmedian(gap))

    h = H_PRIMARY
    results = {}

    def config(c, rule, lab_key=None, ti_thr=TI_THR, at_col="at1_m", plac_kind="pct", clusters="include", hh=h):
        r = apply_rule(F[c], rule, ti_thr, at_col)
        real, plac = frames(ep, F[c], r, LAB[lab_key or (c, "mid", 1)], hh, plac_kind, clusters)
        h2 = h2_rows(real, plac, hh)
        gate, et, g_pre = full_gate(real, lean, hh)
        gs = g_stats(gate, g_pre)
        return {"real": real, "plac": plac, "h2": h2, "gate": gate, "edge": et, "g_pre": g_pre, "gs": gs}

    prim = config("B15", "1s")
    results["primary"] = prim
    h2v = h2_verdict(prim["h2"])
    gv = g_verdict(prim["gate"], prim["gs"])

    # S2-L (clock M60) and X2 (clock B15)
    lifts = []
    m60 = pd.concat([ep, F["M60"]], axis=1)
    m60["Y_level_1s"] = LAB[("M60", "mid", 1)]["level"]
    m60["oi_sign"] = np.nan_to_num(np.sign(m60["oi_d5c"]), nan=0.0)
    base_m60 = LEVEL_NUMS + ["TI_into", "cl_t", "vz_t", "pen_t", "atsz_t", "oi_sign"]
    b15 = pd.concat([ep, F["B15"]], axis=1)
    b15["Y_level_1s"] = LAB[("B15", "mid", 1)]["level"]
    base_b15 = LEVEL_NUMS + ["TI_into_w", "cl_w", "vz_w", "pen_w", "atsz_w", "oi_sign_w"]
    lift_boot = {}
    for nm, fr, bn in (("S2-L (M60, primary)", m60, base_m60), ("X2 (B15)", b15, base_b15)):
        use = fr["tape_ok"] & fr["eligible"]
        for grp, sub in (("real", fr[use & (fr["kind"] == "real")]), ("placebo", fr[use & (fr["kind"] == "pct") & ~fr["placebo_dropped"]])):
            res, boots = lift(sub, bn, TAPE_NUMS, "Y_level_1s")
            lift_boot[(nm, grp)] = boots
            lifts.append({"analysis": nm, "group": grp, **res})
        for k in ("dLL", "dBrier"):
            b = lift_boot[(nm, "real")][k] - lift_boot[(nm, "placebo")][k]
            r_ = [x for x in lifts if x["analysis"] == nm and x["group"] == "real"][0]
            p_ = [x for x in lifts if x["analysis"] == nm and x["group"] == "placebo"][0]
            lo, hi = s1.pct(b, 2.5, 97.5)
            lifts.append({"analysis": nm, "group": f"real_minus_placebo_{k}", k: r_[k] - p_[k], f"{k}_lo95": lo, f"{k}_hi95": hi})
    lift_df = pd.DataFrame(lifts)
    lp = lift_df[(lift_df["analysis"] == "S2-L (M60, primary)") & (lift_df["group"] == "real")].iloc[0]
    rp = lift_df[(lift_df["analysis"] == "S2-L (M60, primary)") & (lift_df["group"] == "real_minus_placebo_dLL")].iloc[0]
    lv = {"VALIDATE_PASS": bool(lp["dLL_lo95"] > 0), "dLL": lp["dLL"], "dLL_lo95": lp["dLL_lo95"], "dLL_hi95": lp["dLL_hi95"],
          "real_minus_placebo_dLL": rp["dLL"], "real_minus_placebo_lo95": rp["dLL_lo95"], "real_minus_placebo_hi95": rp["dLL_hi95"]}

    # X1 grid
    grid = []
    for c in ("B15", "M60"):
        for rule in ("1s", "bar"):
            res = prim if (c, rule) == ("B15", "1s") else config(c, rule)
            results[f"grid_{c}_{rule}"] = res
            for row in res["h2"].to_dict("records"):
                a = res["gs"][(res["gs"]["split"] == row["split"]) & (res["gs"]["group"] == "AGREE")].iloc[0]
                grid.append({"clock": c, "rule": rule, **{k: row[k] for k in ("split", "H", "n_real_confirm", "n_real_other",
                             "n_plac_confirm", "n_plac_other", "delta_real", "delta_plac", "I", "I_lo975", "I_hi975", "mde_I")},
                             "edge_ok_cells": ";".join(res["edge"].loc[res["edge"]["edge_ok"], "cell"]),
                             "n_AGREE": a["n"], "mean_AGREE_primary": a["mean_ynet_primary"], "AGREE_lo95": a["lo95"],
                             **{f"AGREE_fee_{fee:.2f}": a[f"mean_fee_{fee:.2f}"] for fee in FEES}})
    grid_df = pd.DataFrame(grid)

    # X3 fake-level G
    edge_cells = set(prim["edge"].loc[prim["edge"]["edge_ok"], "cell"])
    lean_cells = {"|".join(map(str, k)) for k in lean}
    fake = []
    for scope, cellset in (("EDGE_OK lean cells (pre-registered)", edge_cells), ("all lean cells (extension)", lean_cells)):
        for grp, e in (("real", prim["real"]), ("placebo", prim["plac"])):
            e = e[e["clock_ok"]].copy()
            keys = s1.cell_key(e)
            e["cell"] = ["|".join(map(str, k)) for k in keys]
            e["H_L"] = [lean.get(k, "NONE") for k in keys]
            e = e[e["cell"].isin(cellset)]
            HL = e["H_L"].to_numpy()
            pick = lambda a, b: np.where(HL == "RESPECT", e[a], e[b]).astype(bool)  # noqa: E731
            m = pick("confirm_RESPECT", "confirm_BREAK") & ~pick("veto_RESPECT", "veto_BREAK") & ~e["liq_veto_5m"].to_numpy(bool) \
                & e["print_ok"].to_numpy(bool) & ~pick("sbr_RESPECT", "sbr_BREAK")
            e = add_net(e[m].copy(), h)
            for sp in SCORED:
                x = e[e["split"] == sp]
                pt, b = s1.boot_mean(sp, x["date"].tolist(), x["Y_net_primary"].to_numpy())
                lo, hi = s1.pct(b, 2.5, 97.5)
                fake.append({"scope": scope, "group": grp, "split": sp, "n": int(np.isfinite(x["Y_net_primary"]).sum()),
                             "mean_primary": pt, "lo95": lo, "hi95": hi,
                             **{f"mean_fee_{fee:.2f}": float(np.nanmean(x[f"Y_net_{fee:.2f}"])) if len(x) else np.nan for fee in FEES}})
    fake_df = pd.DataFrame(fake)

    # X4 horizons: H2 per horizon; primary AGREE set at each horizon
    hz = []
    for hh in HORIZONS:
        for row in h2_rows(prim["real"], prim["plac"], hh).to_dict("records"):
            hz.append({"what": "H2", "h_sec": hh, **{k: row[k] for k in ("split", "H", "delta_real", "delta_plac", "I", "I_lo975", "I_hi975")}})
        g = add_net(prim["gate"].copy(), hh)
        for sp in SCORED:
            x = g[(g["split"] == sp) & g["AGREE"]]
            pt, b = s1.boot_mean(sp, x["date"].tolist(), x["Y_net_primary"].to_numpy())
            lo, hi = s1.pct(b, 2.5, 97.5)
            hz.append({"what": "AGREE (primary gate)", "h_sec": hh, "split": sp, "n": int(np.isfinite(x["Y_net_primary"]).sum()),
                       "mean_primary": pt, "lo95": lo, "hi95": hi,
                       **{f"mean_fee_{fee:.2f}": float(np.nanmean(x[f"Y_net_{fee:.2f}"])) if len(x) else np.nan for fee in FEES}})
    hz_df = pd.DataFrame(hz)

    # robustness (section 12)
    rob_specs = [("primary (B15)", {}), ("W = 5 s", {"c": "B5"}), ("W = 30 s", {"c": "B30"}), ("W = 60 s", {"c": "B60"}),
                 ("at-level band 2 bp", {"at_col": "at2_m"}), ("mid proxy = last trade", {"lab_key": ("B15", "last", 1)}),
                 ("entry latency 0 s", {"lab_key": ("B15", "mid", 0)}), ("TI_into_w >= 0.10", {"ti_thr": 0.10}),
                 ("TI_into_w >= 0.30", {"ti_thr": 0.30}), ("sigma placebos", {"plac_kind": "sigma"}),
                 ("clusters excluded", {"clusters": "exclude"})]
    rob = []
    for nm, kw in rob_specs:
        c = kw.pop("c", "B15")
        res = prim if nm.startswith("primary") else config(c, "1s", **kw)
        row = {"run": nm, "edge_ok_cells": ";".join(res["edge"].loc[res["edge"]["edge_ok"], "cell"])}
        for H in ("RESPECT", "BREAK"):
            v = res["h2"][(res["h2"]["split"] == "validate") & (res["h2"]["H"] == H)].iloc[0]
            row.update({f"I_{H}": v["I"], f"I_{H}_lo975": v["I_lo975"], f"delta_real_{H}": v["delta_real"],
                        f"n_real_confirm_{H}": v["n_real_confirm"]})
        a = res["gs"][(res["gs"]["split"] == "validate") & (res["gs"]["group"] == "AGREE")].iloc[0]
        row.update({"n_AGREE_validate": a["n"], "mean_AGREE_validate": a["mean_ynet_primary"], "AGREE_lo95_validate": a["lo95"],
                    "H2_validate_pass": h2_verdict(res["h2"])["VALIDATE_PASS"], "G_validate_pass": g_verdict(res["gate"], res["gs"])["VALIDATE_PASS"]})
        rob.append(row)
        print("robustness done:", nm, flush=True)
    rob_df = pd.DataFrame(rob)

    # outputs
    prim["h2"].to_csv(os.path.join(args.out, "h2_interaction.csv"), index=False)
    prim["edge"].to_csv(os.path.join(args.out, "edge_table.csv"), index=False)
    gcols = ["event_id", "cluster_id", "gate_event", "split", "box", "date", "open_time", "level_type", "instance_id", "cell", "H_L",
             "s", "L", "clock_ok", "impulse", "conf_HL", "veto_HL", "liq_veto_5m", "cluster_conflict", "print_ok", "absorb_HL",
             "depth_agree", "sbr_HL", "edge_table_ok", "first_fail", "AGREE", "Y_fwd_180", "Y_net_0.00", "Y_net_1.09", "Y_net_2.18",
             "Y_net_primary"]
    gl = prim["gate"][gcols].copy()
    gl["date"] = gl["date"].astype(str)
    gl["gate_tag"] = "GATE_PARTIAL"
    gl.to_parquet(os.path.join(args.out, "gate_log.parquet"), index=False, compression="zstd")
    gsum = []
    for sp in SCORED:
        for k, n in prim["gate"][prim["gate"]["split"] == sp]["first_fail"].value_counts().items():
            gsum.append({"split": sp, "first_fail": k, "events": int(n)})
    pd.DataFrame(gsum).to_csv(os.path.join(args.out, "gate_summary.csv"), index=False)
    prim["gs"].to_csv(os.path.join(args.out, "g_stats.csv"), index=False)
    lift_df.to_csv(os.path.join(args.out, "lift.csv"), index=False)
    grid_df.to_csv(os.path.join(args.out, "grid.csv"), index=False)
    fake_df.to_csv(os.path.join(args.out, "fake_level_g.csv"), index=False)
    hz_df.to_csv(os.path.join(args.out, "horizons.csv"), index=False)
    rob_df.to_csv(os.path.join(args.out, "robustness.csv"), index=False)
    cand = prim["gs"][prim["gs"]["group"] == "pre_EDGE_candidates"]
    cand.to_csv(os.path.join(args.out, "candidates.csv"), index=False)

    epo = ep[["event_id", "kind", "offset_bp", "placebo_dropped", "split", "date", "open_time", "box", "level_type", "L", "s",
              "tsib_bucket", "cluster_id", "instance_id", "clock_ok", "tape_ok", "touch_ok", "tau_ms"]].copy()
    epo["date"] = epo["date"].astype(str)
    for c in ("B15", "M60"):
        for col in ("TI_into_w", "cl_w", "pen_w", "vz_w", "nz_w", "at_level_share", "sweep_into_n", "sweep_away_n", "sweep_through",
                    "absorb", "burst_into", "ti_last5_into", "oi_d5c_w"):
            epo[f"{c}_{col}"] = F[c][col].to_numpy()
        lab = LAB[(c, "mid", 1)]
        for hh in HORIZONS:
            epo[f"{c}_Y1s_{hh}"] = lab[hh]
        epo[f"{c}_Y1s_level"] = lab["level"]
    epo.to_parquet(os.path.join(args.out, "episodes.parquet"), index=False, compression="zstd")

    counts = []
    for sp in SCORED:
        e = ep[ep["split"] == sp]
        for kind in ("real", "pct", "sigma"):
            k = e[(e["kind"] == kind) & ~e["placebo_dropped"] & e["eligible"]]
            counts.append({"split": sp, "kind": kind, "events": int(len(k)), "tape_ok": int(k["tape_ok"].sum()),
                           "tape_na": int((~k["tape_ok"]).sum()), "clock_ok_tape_ok": int((k["clock_ok"] & k["tape_ok"]).sum())})
    pd.DataFrame(counts).to_csv(os.path.join(args.out, "event_counts.csv"), index=False)

    summary = {"spec": "S2-LXT-1S v1.0", "stage": "develop+validate (test split not used)", "scored_splits": SCORED,
               "trades_days": {"requested": len(DAYS), "kept": int((qc["slice"] == "KEPT").sum()),
                               "dropped": qc.loc[qc["slice"] != "KEPT", ["date", "status"]].to_dict("records")},
               "mid_vs_last_median_gap_bp": mid_gap_median_bp,
               "S2_H2": h2v, "S2_G": gv, "S2_L": lv,
               "edge_ok_cells": sorted(edge_cells), "lean_cells": sorted(lean_cells)}
    with open(os.path.join(args.out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(json.dumps({k: summary[k] for k in ("S2_H2", "S2_G", "S2_L")}, indent=2, default=str))


if __name__ == "__main__":
    main()
