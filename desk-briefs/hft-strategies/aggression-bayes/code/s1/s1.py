"""S1-LXF-BAR v1.1: level x bar-flow Bayes on public BTCUSDT klines. PAPER ONLY.

Implements 20261003-s1-level-x-bar-flow-spec.md (v1.1). Section numbers in comments refer to that spec.
No exchange API, no keys, no orders. Inputs are the checksum-verified files written by fetch.py.

Stages (the test split is touched once):
  --stage validate   develop + validate statistics only; test rows are never summarised or written
  --stage test       adds the test split and the section 11 robustness runs
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import zipfile
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from scipy import stats as sps

UTC = dt.timezone.utc
ET = ZoneInfo("America/New_York")
FIRST_DAY = dt.date(2025, 10, 1)
LAST_DAY = dt.date(2026, 10, 1)
T0_MS = int(dt.datetime(2025, 10, 1, tzinfo=UTC).timestamp() * 1000)
DAY_MS = 86_400_000
OI_STEP_MS = 300_000
NY_HOLIDAYS = {
    dt.date(2025, 11, 27), dt.date(2025, 12, 25), dt.date(2026, 1, 1), dt.date(2026, 1, 19),
    dt.date(2026, 2, 16), dt.date(2026, 4, 3), dt.date(2026, 5, 25), dt.date(2026, 6, 19),
    dt.date(2026, 7, 3), dt.date(2026, 9, 7),
}
SPLITS = (
    ("warmup", dt.date(2025, 10, 1), dt.date(2025, 12, 31)),
    ("develop", dt.date(2026, 1, 1), dt.date(2026, 6, 30)),
    ("validate", dt.date(2026, 7, 1), dt.date(2026, 8, 31)),
    ("test", dt.date(2026, 9, 1), dt.date(2026, 10, 1)),
)
SEED = 20261003
NBOOT = 2000
FEES = (0.0, 1.09, 2.18)
PRIMARY_FEE = {"RESPECT": 0.0, "BREAK": 1.09}
STOP_FEE = {"RESPECT": 1.09, "BREAK": 2.18}
LEVEL_TYPES = ("IBH", "IBL", "IBM", "VWAP")
TYPE_PRIORITY = {"VWAP": 0, "IBH": 1, "IBL": 2, "IBM": 3}
PRIMARY_OFFSETS = (25.0, -25.0, 50.0, -50.0)
SIGMA_OFFSETS = (0.5, -0.5, 1.0, -1.0)
TSIB_LABELS = ("15-120", "120-360", "360+")
KLINE_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume",
              "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


def all_days():
    d, out = FIRST_DAY, []
    while d <= LAST_DAY:
        out.append(d)
        d += dt.timedelta(days=1)
    return out


def split_of(day):
    for name, a, b in SPLITS:
        if a <= day <= b:
            return name
    return "out"


@dataclasses.dataclass(frozen=True)
class Cfg:
    name: str = "primary"
    bar_min: int = 1
    arm_k: int = 15
    touch_bp: float = 5.0
    ib_arm_bp: float = 5.0
    vwap_arm_bp: float = 10.0
    vwap_arm_sigma: float = 0.5
    r_bp: float = 10.0
    h_level: int = 30
    ti_thr: float = 0.20
    liq_ti: float = 0.20
    veto_cl_bp: float = 5.0
    h_fwd: tuple = (3, 5, 15, 30)
    h_primary: int = 3
    cal: str = "NONE"
    clusters: str = "include"
    box_mode: str = "BOTH"
    placebo: str = "primary"
    cluster_bp: float = 5.0
    hygiene_bp: float = 10.0


# ----------------------------------------------------------------------------- data


@dataclasses.dataclass
class Bars:
    bar_min: int
    days: list
    O: np.ndarray
    Hi: np.ndarray
    Lo: np.ndarray
    C: np.ndarray
    v: np.ndarray
    tbv: np.ndarray
    n: np.ndarray
    present: np.ndarray
    spot_v: np.ndarray
    spot_tbv: np.ndarray
    oi: np.ndarray

    @property
    def bar_ms(self):
        return self.bar_min * 60_000

    @property
    def per_day(self):
        return 1440 // self.bar_min

    @property
    def N(self):
        return len(self.O)

    def truncate_after(self, day):
        """Copy with every bar after `day` (UTC) removed, for test T1."""
        cut = (self.days.index(day) + 1) * self.per_day
        b = dataclasses.replace(self)
        for f in ("O", "Hi", "Lo", "C", "v", "tbv", "n", "spot_v", "spot_tbv"):
            a = getattr(self, f).copy()
            a[cut:] = np.nan
            setattr(b, f, a)
        p = self.present.copy()
        p[cut:] = False
        b.present = p
        oi = self.oi.copy()
        oi[(self.days.index(day) + 1) * 288:] = np.nan
        b.oi = oi
        return b


def _read_zip_csv(path, header):
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:
            return pd.read_csv(f, header=0 if header else None)


def load_klines(data_dir, dataset, bar_min, spot, manifest, fetch_ok):
    days = all_days()
    per_day = 1440 // bar_min
    bar_ms = bar_min * 60_000
    N = len(days) * per_day
    arr = {k: np.full(N, np.nan) for k in ("O", "Hi", "Lo", "C", "v", "tbv", "n")}
    present = np.zeros(N, bool)
    fmt = {"spot_us_files": 0, "perp_header_files": 0}
    for day in days:
        fn = f"BTCUSDT-{bar_min}m-{day.isoformat()}.zip"
        path = os.path.join(data_dir, dataset, fn)
        if not fetch_ok.get((dataset, day.isoformat()), False) or not os.path.exists(path):
            manifest.append({"dataset": dataset, "date": day.isoformat(), "rows": 0, "status": "MISSING"})
            continue
        with zipfile.ZipFile(path) as z:
            first = z.open(z.namelist()[0]).readline().decode()
        has_header = first.startswith("open_time")
        if spot:
            assert not has_header, f"spot file has a header row: {path}"
        else:
            assert has_header, f"perp file lacks a header row: {path}"
            fmt["perp_header_files"] += 1
        df = _read_zip_csv(path, has_header)
        df.columns = KLINE_COLS
        ot = df["open_time"].to_numpy(np.int64)
        if spot:
            assert (ot >= 10**15).all() and (ot < 10**16).all(), f"spot timestamps not 16-digit µs: {path}"
            ot = ot // 1000
            fmt["spot_us_files"] += 1
        else:
            assert (ot >= 10**12).all() and (ot < 10**13).all(), f"perp timestamps not 13-digit ms: {path}"
        assert ((ot - T0_MS) % bar_ms == 0).all()
        g = (ot - T0_MS) // bar_ms
        ok = (g >= 0) & (g < N)
        g = g[ok]
        arr["O"][g] = df["open"].to_numpy(float)[ok]
        arr["Hi"][g] = df["high"].to_numpy(float)[ok]
        arr["Lo"][g] = df["low"].to_numpy(float)[ok]
        arr["C"][g] = df["close"].to_numpy(float)[ok]
        arr["v"][g] = df["volume"].to_numpy(float)[ok]
        arr["tbv"][g] = df["taker_buy_volume"].to_numpy(float)[ok]
        arr["n"][g] = df["count"].to_numpy(float)[ok]
        present[g] = True
        manifest.append({"dataset": dataset, "date": day.isoformat(), "rows": int(len(df)), "status": "OK"})
    return arr, present, fmt


def load_metrics(data_dir, manifest, fetch_ok):
    days = all_days()
    n = len(days) * 288 + 1
    oi = np.full(n, np.nan)
    per_day_rows = []
    for day in days:
        fn = f"BTCUSDT-metrics-{day.isoformat()}.zip"
        path = os.path.join(data_dir, "metrics", fn)
        if not fetch_ok.get(("metrics", day.isoformat()), False) or not os.path.exists(path):
            manifest.append({"dataset": "metrics", "date": day.isoformat(), "rows": 0, "status": "MISSING"})
            per_day_rows.append({"date": day.isoformat(), "stamps": 0, "off_grid": 0, "duplicates": 0})
            continue
        df = _read_zip_csv(path, True)
        ts = pd.to_datetime(df["create_time"], utc=True)
        ms = ((ts - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(milliseconds=1)).to_numpy(np.int64)
        df = df.assign(ms=ms).sort_values("ms")
        off = ((df["ms"] - T0_MS) % OI_STEP_MS) != 0
        dup = df["ms"].duplicated()
        good = df[~off & ~dup]
        k = ((good["ms"] - T0_MS) // OI_STEP_MS).to_numpy(np.int64)
        m = (k >= 0) & (k < n)
        oi[k[m]] = good["sum_open_interest"].to_numpy(float)[m]
        per_day_rows.append({"date": day.isoformat(), "stamps": int(len(good)), "off_grid": int(off.sum()), "duplicates": int(dup.sum())})
        manifest.append({"dataset": "metrics", "date": day.isoformat(), "rows": int(len(df)), "status": "OK"})
    return oi, pd.DataFrame(per_day_rows)


def resample_spot(spot1, present1, bar_min):
    if bar_min == 1:
        return spot1["v"], spot1["tbv"]
    v = spot1["v"].reshape(-1, bar_min)
    t = spot1["tbv"].reshape(-1, bar_min)
    p = present1.reshape(-1, bar_min).all(axis=1)
    sv = np.where(p, v.sum(axis=1), np.nan)
    st = np.where(p, t.sum(axis=1), np.nan)
    return sv, st


def load_all(data_dir):
    log = pd.read_csv(os.path.join(data_dir, "fetch_log.csv"))
    fetch_ok = {(r.dataset, r.date): r.status == "OK" for r in log.itertuples()}
    manifest = []
    p1, pres1, fmt_p = load_klines(data_dir, "perp_1m", 1, False, manifest, fetch_ok)
    p5, pres5, fmt_p5 = load_klines(data_dir, "perp_5m", 5, False, manifest, fetch_ok)
    s1, spres1, fmt_s = load_klines(data_dir, "spot_1m", 1, True, manifest, fetch_ok)
    oi, metrics_days = load_metrics(data_dir, manifest, fetch_ok)
    sv1, st1 = s1["v"], s1["tbv"]
    sv5, st5 = resample_spot(s1, spres1, 5)
    days = all_days()
    b1 = Bars(1, days, p1["O"], p1["Hi"], p1["Lo"], p1["C"], p1["v"], p1["tbv"], p1["n"], pres1, sv1, st1, oi)
    b5 = Bars(5, days, p5["O"], p5["Hi"], p5["Lo"], p5["C"], p5["v"], p5["tbv"], p5["n"], pres5, sv5, st5, oi)
    man = pd.DataFrame(manifest).merge(
        log.rename(columns={"status": "fetch_status"}), on=["dataset", "date"], how="outer")
    fmt = {"perp_1m_header_files": fmt_p["perp_header_files"], "perp_5m_header_files": fmt_p5["perp_header_files"],
           "spot_1m_us_files": fmt_s["spot_us_files"]}
    return b1, b5, man, metrics_days, fmt


# ----------------------------------------------------------------------------- boxes and levels


def ny_anchor_utc(day):
    return dt.datetime.combine(day, dt.time(9, 30), ET).astimezone(UTC)


def build_boxes(bars):
    bm, per_day = bars.bar_min, bars.per_day
    ib_n, lo, hi_off = 60 // bm, 75 // bm, 30 // bm
    boxes = []
    for di, day in enumerate(bars.days):
        boxes.append({"box": "UTC", "date": day, "g0": di * per_day, "nb": per_day})
        if day.weekday() < 5 and day not in NY_HOLIDAYS:
            a = ny_anchor_utc(day)
            e = dt.datetime.combine(day, dt.time(16, 0), ET).astimezone(UTC)
            a_ms, e_ms = int(a.timestamp() * 1000), int(e.timestamp() * 1000)
            boxes.append({"box": "NY", "date": day, "g0": (a_ms - T0_MS) // bars.bar_ms, "nb": (e_ms - a_ms) // bars.bar_ms})
    for i, b in enumerate(boxes):
        b["box_id"] = i
        b["ib_n"], b["win_lo"], b["win_hi"] = ib_n, lo, b["nb"] - hi_off
        pres = bars.present[b["g0"]:b["g0"] + b["nb"]]
        miss = np.flatnonzero(~pres)
        vu = b["nb"] if miss.size == 0 else int(miss[0])
        b["valid_until"] = 0 if vu < ib_n else vu
        b["ib_complete"] = vu >= ib_n
    return boxes


def box_levels(bars, b):
    sl = slice(b["g0"], b["g0"] + b["nb"])
    O, Hi, Lo, C, v = bars.O[sl], bars.Hi[sl], bars.Lo[sl], bars.C[sl], bars.v[sl]
    ib_n = b["ib_n"]
    tp = (Hi + Lo + C) / 3.0
    ref = O[0] if np.isfinite(O[0]) else np.nanmean(O)
    vv = np.nan_to_num(v)
    x = np.nan_to_num(tp - ref)
    zero = np.zeros(1)
    cv = np.concatenate([zero, np.cumsum(vv)])[:-1]
    s1 = np.concatenate([zero, np.cumsum(vv * x)])[:-1]
    s2 = np.concatenate([zero, np.cumsum(vv * x * x)])[:-1]
    with np.errstate(invalid="ignore", divide="ignore"):
        mx = s1 / cv
        vwap = ref + mx
        var = s2 / cv - mx * mx
    vwap[cv <= 0] = np.nan
    sigma = np.sqrt(np.clip(var, 0, None))
    sigma = np.maximum(sigma, 1e-4 * vwap)
    sigma[~np.isfinite(vwap)] = np.nan
    if b["ib_complete"]:
        ibh, ibl = float(np.max(Hi[:ib_n])), float(np.min(Lo[:ib_n]))
    else:
        ibh = ibl = np.nan
    return {"vwap": vwap, "sigma": sigma, "IBH": ibh, "IBL": ibl, "IBM": (ibh + ibl) / 2.0}


def level_rows(lv, b, placebo_kind, cfg):
    """Rows of (level_type, offset, L array, arming threshold array bp, arm_start). Section 5.2."""
    nb, ib_n = b["nb"], b["ib_n"]
    base = {}
    for t in ("IBH", "IBL", "IBM"):
        a = np.full(nb, lv[t])
        a[:ib_n] = np.nan
        base[t] = a
    base["VWAP"] = lv["vwap"]
    sig = lv["sigma"]
    rows = []

    def add(t, off, L):
        if t == "VWAP":
            with np.errstate(invalid="ignore", divide="ignore"):
                thr = np.maximum(cfg.vwap_arm_bp, cfg.vwap_arm_sigma * sig / L * 1e4)
            start = 0
        else:
            thr = np.full(nb, cfg.ib_arm_bp)
            start = ib_n
        rows.append((t, off, L, thr, start))

    if placebo_kind == "real":
        for t in LEVEL_TYPES:
            add(t, 0.0, base[t])
    elif placebo_kind == "pct":
        for t in LEVEL_TYPES:
            for o in PRIMARY_OFFSETS:
                add(t, o, base[t] * (1 + o * 1e-4))
    elif placebo_kind == "sigma":
        for t in LEVEL_TYPES:
            for f in SIGMA_OFFSETS:
                add(t, f, base[t] + f * sig)
    return rows


def detect(rows, bars, b, cfg):
    """Section 5: arming and touch events. Returns list of (row_idx, k, s, d_t)."""
    nb, K = b["nb"], cfg.arm_k
    if b["valid_until"] == 0 or not rows:
        return []
    sl = slice(b["g0"], b["g0"] + nb)
    Hi, Lo, v = bars.Hi[sl], bars.Lo[sl], bars.v[sl]
    L = np.vstack([r[2] for r in rows])
    thr = np.vstack([r[3] for r in rows])
    start = np.array([r[4] for r in rows])[:, None]
    k = np.arange(nb)[None, :]
    with np.errstate(invalid="ignore", divide="ignore"):
        d_up = (Lo[None, :] - L) / L * 1e4
        d_dn = (L - Hi[None, :]) / L * 1e4
    base_ok = (k >= start) & (k < b["valid_until"]) & np.isfinite(L)
    out = []
    win = (k >= b["win_lo"]) & (k < b["win_hi"]) & (k < b["valid_until"]) & (np.nan_to_num(v) > 0)[None, :]
    for s, d in ((1, d_up), (-1, d_dn)):
        with np.errstate(invalid="ignore"):
            ok = base_ok & (d > thr)
        cs = np.concatenate([np.zeros((ok.shape[0], 1), int), np.cumsum(ok, axis=1)], axis=1)
        cnt = np.zeros_like(ok, dtype=int)
        cnt[:, K:] = cs[:, K:nb] - cs[:, 0:nb - K]
        armed = cnt == K
        with np.errstate(invalid="ignore"):
            ev = armed & (d <= cfg.touch_bp) & win & np.isfinite(L)
        ri, ki = np.nonzero(ev)
        for r_, k_ in zip(ri, ki):
            out.append((int(r_), int(k_), s, float(d[r_, k_])))
    return out


# ----------------------------------------------------------------------------- per-box context


def impulse_and_ibwidth(bars, boxes):
    """Section 4.4 impulse triggers and the ib_width_rel denominator (section 6.1)."""
    ndays = len(bars.days)
    per_day = bars.per_day
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.abs(np.log(bars.C[1:] / bars.C[:-1]))
    r = np.concatenate([[np.nan], r])
    thr3 = np.full(ndays, np.nan)
    for di in range(ndays):
        if di < 1:
            continue
        lo = max(0, di - 30) * per_day
        seg = r[lo:di * per_day]
        if np.isfinite(seg).any():
            thr3[di] = np.nanpercentile(seg, 99.9)
    hist = {"UTC": [], "NY": []}
    out = {}
    for b in boxes:
        sl = slice(b["g0"], b["g0"] + b["nb"])
        O, Hi, Lo, C = bars.O[sl], bars.Hi[sl], bars.Lo[sl], bars.C[sl]
        ib = b["ib_n"]
        info = {"i1": False, "i2": False, "i3_first": 10**9, "ib_width_rel": np.nan, "thr1": np.nan, "thr2": np.nan}
        refs = hist[b["box"]]
        if b["ib_complete"]:
            st1 = abs(np.log(C[ib - 1] / O[0]))
            ibh, ibl = np.max(Hi[:ib]), np.min(Lo[:ib])
            st2 = (ibh - ibl) / ((ibh + ibl) / 2)
            last60 = refs[-60:]
            if last60:
                info["thr1"] = float(np.percentile([x[0] for x in last60], 90))
                info["thr2"] = float(np.percentile([x[1] for x in last60], 90))
                info["i1"] = bool(st1 >= info["thr1"])
                info["i2"] = bool(st2 >= info["thr2"])
            last20 = refs[-20:]
            if last20:
                info["ib_width_rel"] = float(st2 / np.median([x[1] for x in last20]))
            di = bars.days.index(b["date"])
            if np.isfinite(thr3[di]):
                rr = r[b["g0"] + ib:b["g0"] + b["valid_until"]]
                hit = np.flatnonzero(rr >= thr3[di])
                if hit.size:
                    info["i3_first"] = int(ib + hit[0])
            refs.append((st1, st2))
        out[b["box_id"]] = info
    return out


def robust_z_by_hour(bars, x):
    """(x - median) / (1.4826 MAD) against the same UTC hour over the 20 calendar days before the day (section 7.1)."""
    ndays = len(bars.days)
    bph = bars.per_day // 24
    X = x.reshape(ndays, 24, bph)
    z = np.full_like(X, np.nan)
    for di in range(20, ndays):
        base = X[di - 20:di]
        for h in range(24):
            vals = base[:, h, :].ravel()
            vals = vals[np.isfinite(vals)]
            if vals.size < 2:
                continue
            med = np.median(vals)
            mad = np.median(np.abs(vals - med))
            if mad > 0:
                z[di, h, :] = (X[di, h, :] - med) / (1.4826 * mad)
    return z.ravel()


# ----------------------------------------------------------------------------- event table


def build_events(bars, boxes, cfg, kinds=("real", "pct", "sigma")):
    ctx = impulse_and_ibwidth(bars, boxes)
    recs = []
    realL = np.full((bars.N, 8), np.nan)
    for b in boxes:
        lv = box_levels(bars, b)
        b["_lv"] = lv
        col0 = 0 if b["box"] == "UTC" else 4
        for j, t in enumerate(LEVEL_TYPES):
            if t == "VWAP":
                a = lv["vwap"]
            else:
                a = np.full(b["nb"], lv[t])
                a[:b["ib_n"]] = np.nan
            seg = realL[b["g0"]:b["g0"] + b["nb"], col0 + j]
            realL[b["g0"]:b["g0"] + b["nb"], col0 + j] = np.where(np.isfinite(a), a, seg)
        for kind in kinds:
            rows = level_rows(lv, b, kind, cfg)
            for ri, k, s, d in detect(rows, bars, b, cfg):
                t, off, L = rows[ri][0], rows[ri][1], rows[ri][2]
                recs.append((b["box_id"], b["box"], b["date"], b["g0"] + k, k, t, kind, off, L[k], L[k - 1], s, d,
                             lv["vwap"][k], lv["vwap"][k - 30 // bars.bar_min], lv["sigma"][k], b["ib_n"]))
    cols = ["box_id", "box", "date", "g", "k", "level_type", "kind", "offset", "L", "L_tm1", "s", "d_t",
            "vwap_t", "vwap_tm30", "sigma_t", "ib_n"]
    ev = pd.DataFrame.from_records(recs, columns=cols)
    ev = ev.sort_values(["g", "box", "level_type", "kind", "offset"], kind="mergesort").reset_index(drop=True)
    return ev, ctx, realL


def compute_labels(g, s, L, bars, cfg):
    """Y_level (section 6.2) reads closes of bars t..t+H-1; Y_fwd (section 7.3) reads O_{t+1} and C_{t+h}."""
    g, s, L = np.asarray(g), np.asarray(s), np.asarray(L, float)
    N = bars.N
    pres_cs = np.concatenate([[0], np.cumsum(bars.present)])

    def all_present(a, b_):
        ok_ = (a >= 0) & (b_ < N)
        a_c, b_c = np.clip(a, 0, N), np.clip(b_ + 1, 0, N)
        return ok_ & ((pres_cs[b_c] - pres_cs[a_c]) == (b_ - a + 1))

    out = {}
    H = cfg.h_level
    idx_c = np.clip(g[:, None] + np.arange(H)[None, :], 0, N - 1)
    with np.errstate(invalid="ignore"):
        x = s[:, None] * (bars.C[idx_c] - L[:, None]) / L[:, None] * 1e4
    up = x >= cfg.r_bp
    dn = x <= -cfg.r_bp
    first_up = np.where(up.any(1), up.argmax(1), H)
    first_dn = np.where(dn.any(1), dn.argmax(1), H)
    lab = np.where(first_up < first_dn, "RESPECT", np.where(first_dn < first_up, "BREAK", "NONE"))
    out["Y_level"] = np.where(all_present(g, g + H - 1), lab, "NA")
    o1 = bars.O[np.clip(g + 1, 0, N - 1)]
    for h in cfg.h_fwd:
        ch = bars.C[np.clip(g + h, 0, N - 1)]
        with np.errstate(invalid="ignore", divide="ignore"):
            y = s * np.log(ch / o1) * 1e4
        out[f"Y_fwd_{h}"] = np.where(all_present(g + 1, g + h), y, np.nan)
    return out


def add_features(ev, bars, boxes, ctx, cfg, realL, z_v, z_ats):
    bm, bar_ms = bars.bar_min, bars.bar_ms
    g = ev["g"].to_numpy()
    s = ev["s"].to_numpy()
    L = ev["L"].to_numpy()
    Ltm1 = ev["L_tm1"].to_numpy()
    ev["open_time"] = T0_MS + g * bar_ms
    ev["split"] = [split_of(d) for d in ev["date"]]
    ev["is_placebo"] = ev["kind"] != "real"
    ev["offset_bp"] = np.where(ev["kind"] == "pct", ev["offset"], 0.0)
    tsib = (ev["k"] - ev["ib_n"]).to_numpy() * bm
    ev["tsib_min"] = tsib
    ev["tsib_bucket"] = np.where(tsib < 120, TSIB_LABELS[0], np.where(tsib < 360, TSIB_LABELS[1], TSIB_LABELS[2]))
    n15 = 15 // bm
    ev["speed15"] = s * (bars.C[g - 1 - n15] - bars.C[g - 1]) / Ltm1 * 1e4
    ev["dist_vwap_sigma"] = (bars.C[g - 1] - ev["vwap_t"].to_numpy()) / ev["sigma_t"].to_numpy()
    ev["ib_width_rel"] = [ctx[i]["ib_width_rel"] for i in ev["box_id"]]
    ev["vwap_slope30"] = (ev["vwap_t"].to_numpy() - ev["vwap_tm30"].to_numpy()) / Ltm1 * 1e4
    ts = pd.to_datetime(ev["open_time"], unit="ms", utc=True)
    ev["hour_utc"] = ts.dt.hour.to_numpy()
    ev["dow"] = ts.dt.dayofweek.to_numpy()
    et = ts.dt.tz_convert(ET)
    eh = et.dt.hour.to_numpy()
    ev["regime_tag"] = np.where(eh == 16, "post_cash", np.where(eh == 17, "cme_break", "other"))
    # instances and touch_seq (section 5.4)
    key_ib = ev["box"] + "|" + ev["date"].astype(str) + "|" + ev["level_type"] + "|" + ev["kind"] + "|" + ev["offset"].astype(str)
    is_vwap = ev["level_type"] == "VWAP"
    ev["instance_id"] = np.where(is_vwap, key_ib + "|" + ev["g"].astype(str), key_ib)
    ev["touch_seq"] = ev.groupby(key_ib).cumcount()
    # burst features (section 7.1)
    v, tbv = bars.v[g], bars.tbv[g]
    with np.errstate(invalid="ignore", divide="ignore"):
        ti = (2 * tbv - v) / v
        sv, st = bars.spot_v[g], bars.spot_tbv[g]
        ti_spot = np.where(sv > 0, (2 * st - sv) / sv, np.nan)
    ev["TI_t"] = ti
    ev["TI_into"] = -s * ti
    ev["pen_t"] = -ev["d_t"]
    p = ev["pen_t"].to_numpy()
    ev["pen_class"] = np.where(p > 5, "PIERCE", np.where(p >= 0, "KISS", "NEAR"))
    ev["cl_t"] = s * (bars.C[g] - L) / L * 1e4
    ev["vz_t"] = z_v[g]
    ev["atsz_t"] = z_ats[g]
    dec = ev["open_time"].to_numpy() + bar_ms
    kk = (dec - T0_MS) // OI_STEP_MS
    ok = (kk >= 1) & (kk < len(bars.oi))
    kk_c = np.clip(kk, 1, len(bars.oi) - 1)
    oi_d = np.where(ok, bars.oi[kk_c] - bars.oi[kk_c - 1], np.nan)
    ev["oi_d5c"] = oi_d
    ev["oi_na"] = ~np.isfinite(oi_d)
    ev["TI_spot_t"] = ti_spot
    for col, val in compute_labels(g, s, L, bars, cfg).items():
        ev[col] = val
    N = bars.N
    # clock (section 4.6) and box-mode eligibility (section 11)
    imp = []
    clock = []
    for bid, k in zip(ev["box_id"], ev["k"]):
        c = ctx[bid]
        tag = "I1" if c["i1"] else ("I2" if c["i2"] else ("I3" if k >= c["i3_first"] else ""))
        imp.append(tag)
        clock.append(tag == "")
    ev["impulse"] = imp
    cal_ok = np.ones(len(ev), bool)
    if cfg.cal == "PROXY":
        mins = et.dt.hour.to_numpy() * 60 + et.dt.minute.to_numpy()
        wk = et.dt.dayofweek.to_numpy() < 5
        hit = ((mins + 30 > 8 * 60 + 15) & (mins < 9 * 60 + 15)) | ((mins + 30 > 13 * 60 + 45) & (mins < 14 * 60 + 45))
        cal_ok = ~(wk & hit)
    ev["cal_tag"] = cfg.cal
    ev["cal_blocked"] = ~cal_ok
    ev["clock_ok"] = np.array(clock) & cal_ok
    ev["algebra_tag"] = "RECON"
    elig = np.ones(len(ev), bool)
    if cfg.box_mode == "UTC":
        elig = (ev["box"] == "UTC").to_numpy()
    elif cfg.box_mode == "NY":
        elig = (ev["box"] == "NY").to_numpy()
    elif cfg.box_mode == "EXCLUSIVE":
        in_ny = np.zeros(N, bool)
        for b in boxes:
            if b["box"] == "NY":
                in_ny[b["g0"]:b["g0"] + b["nb"]] = True
        elig = ~((ev["box"] == "UTC").to_numpy() & in_ny[g])
    ev["eligible"] = elig
    # placebo hygiene (section 9)
    pl = ev["is_placebo"].to_numpy()
    with np.errstate(invalid="ignore"):
        D = np.abs(realL[g] - L[:, None]) / L[:, None] * 1e4
    dist = np.where(np.isfinite(D), D, np.inf).min(axis=1)
    ev["min_dist_real_bp"] = np.where(pl, dist, np.nan)
    ev["placebo_dropped"] = pl & (dist <= cfg.hygiene_bp)
    # clusters among real events (section 5.4)
    ev["cluster_id"] = -1
    real = ev.index[~ev["is_placebo"]]
    rg = ev.loc[real]
    cid = 0
    cl = np.full(len(ev), -1)
    for gg, grp in rg.groupby("g"):
        if len(grp) < 2:
            continue
        idxs = grp.index.to_numpy()
        Ls = grp["L"].to_numpy()
        parent = list(range(len(idxs)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i in range(len(idxs)):
            for j in range(i + 1, len(idxs)):
                if abs(Ls[i] - Ls[j]) / ((Ls[i] + Ls[j]) / 2) * 1e4 <= cfg.cluster_bp:
                    parent[find(i)] = find(j)
        comps = {}
        for i in range(len(idxs)):
            comps.setdefault(find(i), []).append(idxs[i])
        for members in comps.values():
            if len(members) >= 2:
                cl[members] = cid
                cid += 1
    ev["cluster_id"] = cl
    ev["event_id"] = np.arange(len(ev))
    return ev


# ----------------------------------------------------------------------------- level model (section 6.3)


def cells_all():
    out = []
    for t in LEVEL_TYPES:
        for box in ("UTC", "NY"):
            for s in (1, -1):
                for tb in TSIB_LABELS:
                    if box == "NY" and tb == "360+":
                        continue
                    out.append((t, box, s, tb))
    return out


def bb_mom(nR, n):
    m = n > 0
    if m.sum() == 0:
        return np.nan, np.nan
    p = nR[m] / n[m]
    mu = nR[m].sum() / n[m].sum()
    if mu <= 0 or mu >= 1:
        return np.nan, np.nan
    s2 = np.mean((p - mu) ** 2)
    h = np.mean(1.0 / n[m])
    rho = (s2 / (mu * (1 - mu)) - h) / (1 - h) if h < 1 else 1e-6
    rho = float(np.clip(rho, 1e-6, 1 - 1e-6))
    ab = 1.0 / rho - 1.0
    return mu * ab, (1 - mu) * ab


def bh(p):
    p = np.asarray(p, float)
    n = len(p)
    if n == 0:
        return p
    o = np.argsort(p)
    q = p[o] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty(n)
    out[o] = np.minimum(q, 1.0)
    return out


def cell_key(df):
    return list(zip(df["level_type"], df["box"], df["s"], df["tsib_bucket"]))


def fit_level_model(h1ev, splits):
    """h1ev: real, clock_ok, eligible events of the scored splits. Returns the per-cell table."""
    rows = []
    cnt = {}
    for sp in splits:
        e = h1ev[h1ev["split"] == sp]
        for key, grp in e.groupby(["level_type", "box", "s", "tsib_bucket"]):
            y = grp["Y_level"]
            cnt[(sp,) + key] = (int((y == "RESPECT").sum()), int((y == "BREAK").sum()), int((y == "NONE").sum()), int((y == "NA").sum()))
    dev = {c: cnt.get(("develop",) + c, (0, 0, 0, 0)) for c in cells_all()}
    prior = {}
    for t in LEVEL_TYPES:
        cs = [c for c in cells_all() if c[0] == t]
        nR = np.array([dev[c][0] for c in cs], float)
        n = np.array([dev[c][0] + dev[c][1] for c in cs], float)
        prior[t] = bb_mom(nR, n)
    populated = [c for c in cells_all() if dev[c][0] + dev[c][1] >= 1]
    pvals = [sps.binomtest(dev[c][0], dev[c][0] + dev[c][1], 0.5).pvalue for c in populated]
    qv = dict(zip(populated, bh(pvals)))
    pv = dict(zip(populated, pvals))
    for c in cells_all():
        nR, nB, nN, nNA = dev[c]
        a, b_ = prior[c[0]]
        n = nR + nB
        phat = (nR + a) / (n + a + b_) if np.isfinite(a) else (nR / n if n else np.nan)
        lean = bool(c in qv and qv[c] < 0.10 and abs(phat - 0.5) >= 0.05 and n >= 100)
        H_L = ("RESPECT" if phat > 0.5 else "BREAK") if lean else "NONE"
        row = {"level_type": c[0], "box": c[1], "s": c[2], "tsib_bucket": c[3], "populated": c in qv,
               "dev_nR": nR, "dev_nB": nB, "dev_nNONE": nN, "dev_nNA": nNA,
               "dev_raw_share": nR / n if n else np.nan, "prior_alpha": a, "prior_beta": b_, "p_hat": phat,
               "dev_binom_p": pv.get(c, np.nan), "dev_bh_q": qv.get(c, np.nan), "lean": lean, "H_L": H_L}
        for sp in [x for x in splits if x != "develop"]:
            r_, b2, n_, na_ = cnt.get((sp,) + c, (0, 0, 0, 0))
            nn = r_ + b2
            row[f"{sp}_nR"], row[f"{sp}_nB"], row[f"{sp}_nNONE"], row[f"{sp}_nNA"] = r_, b2, n_, na_
            row[f"{sp}_raw_share"] = r_ / nn if nn else np.nan
            if lean and nn:
                alt = "greater" if H_L == "RESPECT" else "less"
                row[f"{sp}_binom_p_1s"] = sps.binomtest(r_, nn, 0.5, alternative=alt).pvalue
            else:
                row[f"{sp}_binom_p_1s"] = np.nan
        if lean:
            side_ok = lambda sh: (sh > 0.5) if H_L == "RESPECT" else (sh < 0.5)  # noqa: E731
            if "validate" in splits:
                nn = row["validate_nR"] + row["validate_nB"]
                row["validate_pass"] = bool(nn >= 30 and side_ok(row["validate_raw_share"]) and row["validate_binom_p_1s"] < 0.05)
            if "test" in splits:
                nn = row["test_nR"] + row["test_nB"]
                row["test_pass"] = bool(nn >= 15 and side_ok(row["test_raw_share"]))
        else:
            if "validate" in splits:
                row["validate_pass"] = False
            if "test" in splits:
                row["test_pass"] = False
        rows.append(row)
    tab = pd.DataFrame(rows)
    if "test" in splits:
        tab["h1_cell_pass"] = tab["lean"].astype(bool) & tab["validate_pass"].astype(bool) & tab["test_pass"].astype(bool)
    else:
        tab["h1_cell_pass"] = False
    return tab, prior


# ----------------------------------------------------------------------------- bootstrap helpers


def split_days(sp):
    for name, a, b in SPLITS:
        if name == sp:
            out, d = [], a
            while d <= b:
                out.append(d)
                d += dt.timedelta(days=1)
            return out
    raise KeyError(sp)


_W_CACHE = {}


def boot_W(sp):
    if sp not in _W_CACHE:
        nd = len(split_days(sp))
        rng = np.random.default_rng(SEED)
        idx = rng.integers(0, nd, size=(NBOOT, nd))
        W = np.zeros((NBOOT, nd))
        for i in range(NBOOT):
            W[i] = np.bincount(idx[i], minlength=nd)
        _W_CACHE[sp] = W
    return _W_CACHE[sp]


def day_index(dates, sp):
    pos = {d: i for i, d in enumerate(split_days(sp))}
    return np.array([pos[d] for d in dates], int)


def sums(di, y, nd):
    y = np.asarray(y, float)
    m = np.isfinite(y)
    return np.bincount(di[m], weights=y[m], minlength=nd), np.bincount(di[m], minlength=nd).astype(float)


def boot_mean(sp, dates, y):
    nd = len(split_days(sp))
    if len(y) == 0:
        return np.nan, np.full(NBOOT, np.nan)
    di = day_index(dates, sp)
    S, Nn = sums(di, y, nd)
    W = boot_W(sp)
    with np.errstate(invalid="ignore", divide="ignore"):
        b = (W @ S) / (W @ Nn)
    point = S.sum() / Nn.sum() if Nn.sum() else np.nan
    return point, b


def pct(b, lo, hi):
    b = b[np.isfinite(b)]
    if b.size == 0:
        return np.nan, np.nan
    return float(np.percentile(b, lo)), float(np.percentile(b, hi))


# ----------------------------------------------------------------------------- burst classification and H2


def classify(ev, cfg):
    ti_into, cl, vz, ti = ev["TI_into"], ev["cl_t"], ev["vz_t"], ev["TI_t"]
    agg = ti_into >= cfg.ti_thr
    ev["confirm_BREAK"] = agg & (cl < 0) & (vz >= 0)
    ev["confirm_RESPECT"] = agg & (cl >= 0) & (vz >= 0)
    ev["veto_BREAK"] = agg & (cl >= 0)
    ev["veto_RESPECT"] = agg & (cl < -cfg.veto_cl_bp)
    ev["liq_veto_5m"] = (ev["oi_d5c"] < 0) & (ti.abs() >= cfg.liq_ti)
    return ev


def h2_split(real, plac, sp, h, extra_filter=None):
    out = []
    W = boot_W(sp)
    nd = W.shape[1]
    r = real[real["split"] == sp]
    p = plac[plac["split"] == sp]
    if extra_filter is not None:
        r, p = extra_filter(r), extra_filter(p)
    col = f"Y_fwd_{h}"
    for H in ("RESPECT", "BREAK"):
        sign = 1.0 if H == "RESPECT" else -1.0
        res = {"split": sp, "H": H, "h": h}
        parts = {}
        for nm, e in (("real", r), ("plac", p)):
            y = sign * e[col].to_numpy()
            conf = e[f"confirm_{H}"].to_numpy(bool)
            di = day_index(e["date"].tolist(), sp) if len(e) else np.zeros(0, int)
            Sc, Nc = sums(di[conf], y[conf], nd) if len(e) else (np.zeros(nd), np.zeros(nd))
            Sn, Nn = sums(di[~conf], y[~conf], nd) if len(e) else (np.zeros(nd), np.zeros(nd))
            with np.errstate(invalid="ignore", divide="ignore"):
                pt = Sc.sum() / Nc.sum() - Sn.sum() / Nn.sum()
                bt = (W @ Sc) / (W @ Nc) - (W @ Sn) / (W @ Nn)
            parts[nm] = (pt, bt)
            res[f"n_{nm}_confirm"] = int(Nc.sum())
            res[f"n_{nm}_other"] = int(Nn.sum())
            res[f"mean_{nm}_confirm"] = Sc.sum() / Nc.sum() if Nc.sum() else np.nan
            res[f"mean_{nm}_other"] = Sn.sum() / Nn.sum() if Nn.sum() else np.nan
        res["delta_real"] = parts["real"][0]
        res["delta_plac"] = parts["plac"][0]
        res["I"] = parts["real"][0] - parts["plac"][0]
        bI = parts["real"][1] - parts["plac"][1]
        res["I_lo95"], res["I_hi95"] = pct(bI, 2.5, 97.5)
        res["I_lo975"], res["I_hi975"] = pct(bI, 1.25, 98.75)
        res["delta_real_lo95"], res["delta_real_hi95"] = pct(parts["real"][1], 2.5, 97.5)
        se = float(np.nanstd(bI, ddof=1)) if np.isfinite(bI).sum() > 1 else np.nan
        res["I_boot_se"] = se
        res["mde_I"] = 2.8 * se
        out.append(res)
    return out


# ----------------------------------------------------------------------------- gate (section 8)


def run_gate(real, cells, edge_ok_cells, use_edge):
    """Sequential gate over real events. Returns per-event flags. `edge_ok_cells`: set of cell keys."""
    lean = {(r.level_type, r.box, r.s, r.tsib_bucket): r.H_L for r in cells.itertuples() if r.lean}
    e = real.copy()
    keys = cell_key(e)
    e["H_L"] = [lean.get(k, "NONE") for k in keys]
    e["cell"] = ["|".join(map(str, k)) for k in keys]
    HL = e["H_L"].to_numpy()
    conf = np.where(HL == "RESPECT", e["confirm_RESPECT"], np.where(HL == "BREAK", e["confirm_BREAK"], False))
    veto = np.where(HL == "RESPECT", e["veto_RESPECT"], np.where(HL == "BREAK", e["veto_BREAK"], False))
    e["conf_HL"] = conf.astype(bool)
    e["veto_HL"] = veto.astype(bool)
    e["print_confirm"] = (e["vz_t"] >= 0).to_numpy()
    e["depth_agree"] = "NT"
    e["edge_ok"] = [("|".join(map(str, k)) in edge_ok_cells) if use_edge else True for k in keys]
    # clusters: one gate event per cluster
    e["gate_event"] = True
    e["cluster_conflict"] = False
    e["cluster_members"] = 1
    for cid, grp in e[e["cluster_id"] >= 0].groupby("cluster_id"):
        order = sorted(grp.index, key=lambda i: (not e.at[i, "clock_ok"], e.at[i, "H_L"] == "NONE",
                                                  TYPE_PRIORITY[e.at[i, "level_type"]], e.at[i, "box"] != "UTC"))
        rep = order[0]
        hyp = {(e.at[i, "H_L"], e.at[i, "s"]) for i in grp.index if e.at[i, "clock_ok"] and e.at[i, "H_L"] != "NONE"}
        e.loc[grp.index, "gate_event"] = False
        e.at[rep, "gate_event"] = True
        e.at[rep, "cluster_conflict"] = len(hyp) > 1
        e.at[rep, "cluster_members"] = len(grp)
    member_inst = e.groupby("cluster_id")["instance_id"].apply(list).to_dict()
    spent = set()
    reason, agree, ia = [], [], []
    for i in e.index:
        r = e.loc[i]
        if not r["gate_event"]:
            reason.append("CLUSTER_DUP")
            agree.append(False)
            ia.append(False)
            continue
        if not r["clock_ok"]:
            reason.append("CLOCK_OK:" + ("CAL" if r["cal_blocked"] and r["impulse"] == "" else "IMPULSE_" + r["impulse"]))
            agree.append(False)
            ia.append(False)
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
            agree.append(False)
            ia.append(False)
            continue
        ia.append(True)
        if not r["print_confirm"]:
            reason.append("PRINT_CONFIRM")
            agree.append(False)
            continue
        if not r["edge_ok"]:
            reason.append("EDGE_OK")
            agree.append(False)
            continue
        reason.append("AGREE")
        agree.append(True)
        spent.add(r["instance_id"])
        if r["cluster_id"] >= 0:
            spent.update(member_inst.get(r["cluster_id"], []))
    e["independent_agree"] = ia
    e["first_fail"] = reason
    e["AGREE"] = agree
    return e


def add_ynet(g, h):
    sign = np.where(g["H_L"] == "RESPECT", 1.0, np.where(g["H_L"] == "BREAK", -1.0, np.nan))
    y = sign * g[f"Y_fwd_{h}"].to_numpy()
    g["Y_dir"] = y
    for f in FEES:
        g[f"Y_net_{f:.2f}"] = y - f
    g["fee_primary"] = np.where(g["H_L"] == "BREAK", PRIMARY_FEE["BREAK"], PRIMARY_FEE["RESPECT"])
    g["Y_net_primary"] = y - g["fee_primary"]
    return g


def edge_table(g_pre, cfg):
    """EDGE_OK proxy: develop lower 95% bound of mean Y_net(3) at the primary fee, per lean cell,
    over develop gate events that pass CLOCK_OK, INDEPENDENT_AGREE and PRINT_CONFIRM."""
    rows = []
    d = g_pre[(g_pre["split"] == "develop") & (g_pre["H_L"] != "NONE")]
    for cell, grp in d.groupby("cell"):
        cand = grp[grp["first_fail"] == "AGREE"]
        pt, b = boot_mean("develop", cand["date"].tolist(), cand["Y_net_primary"].to_numpy())
        lo, hi = pct(b, 2.5, 97.5) if len(cand) else (np.nan, np.nan)
        allc = grp[grp["clock_ok"] & grp["gate_event"]]
        pt2, b2 = boot_mean("develop", allc["date"].tolist(), allc["Y_net_primary"].to_numpy())
        lo2, _ = pct(b2, 2.5, 97.5) if len(allc) else (np.nan, np.nan)
        rows.append({"cell": cell, "H_L": grp["H_L"].iloc[0], "n_candidates": int(np.isfinite(cand["Y_net_primary"]).sum()),
                     "mean_ynet3": pt, "lo95": lo, "hi95": hi, "edge_ok": bool(np.isfinite(lo) and lo > 0),
                     "sens_all_cell_events_n": int(np.isfinite(allc["Y_net_primary"]).sum()), "sens_all_cell_events_mean": pt2,
                     "sens_all_cell_events_lo95": lo2})
    return pd.DataFrame(rows, columns=["cell", "H_L", "n_candidates", "mean_ynet3", "lo95", "hi95", "edge_ok",
                                       "sens_all_cell_events_n", "sens_all_cell_events_mean", "sens_all_cell_events_lo95"])


# ----------------------------------------------------------------------------- one full run


def analysis_frames(ev, cfg):
    real = ev[(~ev["is_placebo"]) & ev["eligible"]].copy()
    if cfg.clusters == "exclude":
        real = real[real["cluster_id"] < 0].copy()
    kind = "pct" if cfg.placebo == "primary" else "sigma"
    plac = ev[(ev["kind"] == kind) & ev["eligible"] & (~ev["placebo_dropped"])].copy()
    return real, plac


def run(bars, cfg, scored, z_v=None, z_ats=None, events=None):
    boxes = build_boxes(bars)
    if events is None:
        if z_v is None:
            with np.errstate(divide="ignore", invalid="ignore"):
                lv = np.where(bars.v > 0, np.log(bars.v), np.nan)
                la = np.where((bars.v > 0) & (bars.n > 0), np.log(bars.v / bars.n), np.nan)
            z_v, z_ats = robust_z_by_hour(bars, lv), robust_z_by_hour(bars, la)
        ev, ctx, realL = build_events(bars, boxes, cfg)
        ev = add_features(ev, bars, boxes, ctx, cfg, realL, z_v, z_ats)
    else:
        ev = events
    ev = classify(ev, cfg)
    real, plac = analysis_frames(ev, cfg)
    h = cfg.h_primary
    real_clock = real[real["clock_ok"]]
    plac_clock = plac[plac["clock_ok"]]
    h1ev = real_clock[real_clock["split"].isin(scored)]
    cells, prior = fit_level_model(h1ev, scored)
    # gate pass 1 (no EDGE) -> EDGE table from develop -> gate pass 2
    g_pre = add_ynet(run_gate(real, cells, set(), use_edge=False), h)
    et = edge_table(g_pre, cfg)
    edge_cells = set(et.loc[et["edge_ok"], "cell"])
    gate = add_ynet(run_gate(real, cells, edge_cells, use_edge=True), h)
    h2 = []
    for sp in scored:
        if sp == "warmup":
            continue
        h2 += h2_split(real_clock, plac_clock, sp, h)
    return {"events": ev, "cells": cells, "prior": prior, "edge": et, "gate": gate,
            "h2": pd.DataFrame(h2), "real": real, "plac": plac, "boxes": boxes, "z": (z_v, z_ats)}


# ----------------------------------------------------------------------------- summaries


def h1_verdict(cells, scored):
    lean = cells[cells["lean"]]
    out = {"n_populated": int(cells["populated"].sum()), "n_lean_develop": int(len(lean)),
           "lean_cells": ";".join(f"{r.level_type}|{r.box}|{r.s}|{r.tsib_bucket}:{r.H_L}" for r in lean.itertuples())}
    if "validate" in scored:
        out["n_lean_validate_pass"] = int(cells["validate_pass"].sum())
    if "test" in scored:
        out["n_cells_pass_all"] = int(cells["h1_cell_pass"].sum())
        out["PASS"] = bool(cells["h1_cell_pass"].any())
    return out


def h2_verdict(h2, scored):
    if "test" not in scored:
        return {}
    ok = {}
    for H in ("RESPECT", "BREAK"):
        v = h2[(h2["H"] == H) & (h2["split"] == "validate")].iloc[0]
        t = h2[(h2["H"] == H) & (h2["split"] == "test")].iloc[0]
        ok[H] = bool(v["I_lo975"] > 0 and v["delta_real"] > 0 and t["I_lo975"] > 0 and t["delta_real"] > 0)
    return {"PASS": any(ok.values()), "pass_RESPECT": ok["RESPECT"], "pass_BREAK": ok["BREAK"]}


def g_stats(gate, scored, h1_pass):
    rows = []
    for sp in scored:
        if sp == "warmup":
            continue
        gs = gate[(gate["split"] == sp) & gate["gate_event"]]
        ag = gs[gs["AGREE"]]
        fw = gs[gs["clock_ok"] & (gs["H_L"] != "NONE") & (~gs["AGREE"])]
        for nm, e in (("AGREE", ag), ("lean_FLAT_WATCH", fw)):
            y = e["Y_net_primary"].to_numpy()
            pt, b = boot_mean(sp, e["date"].tolist(), y)
            lo, hi = pct(b, 2.5, 97.5)
            row = {"split": sp, "group": nm, "n": int(np.isfinite(y).sum()), "mean_ynet3_primary": pt, "lo95": lo, "hi95": hi,
                   "n_RESPECT": int((e["H_L"] == "RESPECT").sum()), "n_BREAK": int((e["H_L"] == "BREAK").sum())}
            for f in FEES:
                row[f"mean_ynet3_fee_{f:.2f}"] = float(np.nanmean(e[f"Y_net_{f:.2f}"])) if len(e) else np.nan
            rows.append(row)
    gs = pd.DataFrame(rows)
    verdict = {}
    if "test" in scored and len(gs):
        v = gs[(gs["split"] == "validate") & (gs["group"] == "AGREE")].iloc[0]
        t = gs[(gs["split"] == "test") & (gs["group"] == "AGREE")].iloc[0]
        pool = gate[gate["split"].isin(["validate", "test"]) & gate["AGREE"]]
        y = pool["Y_net_primary"]
        tot = y.sum()
        ts = pd.to_datetime(pool["open_time"], unit="ms", utc=True)
        conc_ok = True
        mshare = hshare = np.nan
        if len(pool) and tot > 0:
            mshare = float(y.groupby(ts.dt.strftime("%Y-%m").to_numpy()).sum().max() / tot)
            hshare = float(y.groupby(ts.dt.hour.to_numpy()).sum().max() / tot)
            conc_ok = mshare <= 0.5 and hshare <= 0.5
        conds = {
            "h1_pass": bool(h1_pass),
            "n_validate_ge_30": bool(v["n"] >= 30),
            "n_test_ge_15": bool(t["n"] >= 15),
            "validate_mean_gt_0": bool(v["mean_ynet3_primary"] > 0),
            "validate_lo95_gt_0": bool(v["lo95"] > 0),
            "test_mean_gt_0": bool(t["mean_ynet3_primary"] > 0),
            "concentration_ok": bool(conc_ok and len(pool) > 0 and tot > 0),
        }
        verdict = {"PASS": all(conds.values()), **conds, "max_month_share": mshare, "max_hour_share": hshare}
    return gs, verdict


def gate_summary(gate, scored):
    rows = []
    for sp in scored:
        if sp == "warmup":
            continue
        e = gate[gate["split"] == sp]
        vc = e["first_fail"].value_counts()
        for k, n in vc.items():
            rows.append({"split": sp, "first_fail": k, "events": int(n)})
    return pd.DataFrame(rows)


FAKE_MAP = {
    "CLOCK_OK:IMPULSE_I1": "event bursts (impulse)", "CLOCK_OK:IMPULSE_I2": "event bursts (impulse)",
    "CLOCK_OK:IMPULSE_I3": "event bursts (impulse)", "CLOCK_OK:CAL": "event bursts (calendar)",
    "INDEPENDENT_AGREE:LIQ_VETO": "liq cascades (5 m OI proxy)", "INDEPENDENT_AGREE:EPISODE_ONCE": "touch ping-pong",
    "CLUSTER_DUP": "one sweep scored twice", "INDEPENDENT_AGREE:CLUSTER_CONFLICT": "one sweep scored twice",
    "INDEPENDENT_AGREE:NO_LEAN": "no level lean", "INDEPENDENT_AGREE:NO_CONFIRM": "no flow confirmation",
    "INDEPENDENT_AGREE:VETO": "absorb / closed-through veto", "PRINT_CONFIRM": "low-volume touch (print proxy)",
    "EDGE_OK": "fails fee/markout proxy",
}


def volume_shadow(gate, scored):
    rows = []
    for sp in scored:
        if sp == "warmup":
            continue
        e = gate[gate["split"] == sp]
        rows.append({"split": sp, "category": "episodes (AGREE)", "program_label": "V_qual", "units": int(e["AGREE"].sum())})
        for k, n in e.loc[~e["AGREE"], "first_fail"].value_counts().items():
            rows.append({"split": sp, "category": k, "program_label": FAKE_MAP.get(k, k), "units": int(n)})
        rows.append({"split": sp, "category": "ungated touch-and-follow total", "program_label": "V_units if ungated", "units": int(len(e))})
    return pd.DataFrame(rows)


def logistic_check(real_clock, cells, prior):
    from sklearn.linear_model import LogisticRegression
    d = real_clock[real_clock["Y_level"].isin(["RESPECT", "BREAK"])]
    dev, val = d[d["split"] == "develop"], d[d["split"] == "validate"]
    if len(dev) < 10 or len(val) < 10:
        return {}, pd.DataFrame()
    cats = ["level_type", "box", "s", "tsib_bucket", "hour_utc", "dow"]
    nums = ["speed15", "dist_vwap_sigma", "ib_width_rel", "vwap_slope30", "touch_seq"]

    def design(x, ref):
        X = pd.get_dummies(x[cats].astype(str), drop_first=False)
        ref_cols = pd.get_dummies(ref[cats].astype(str), drop_first=False).columns
        X = X.reindex(columns=ref_cols, fill_value=0).astype(float)
        med = ref[nums].median()
        mu, sd = ref[nums].fillna(med).mean(), ref[nums].fillna(med).std().replace(0, 1)
        Z = (x[nums].fillna(med) - mu) / sd
        return np.hstack([X.to_numpy(), Z.to_numpy()])

    Xd, Xv = design(dev, dev), design(val, dev)
    yd = (dev["Y_level"] == "RESPECT").to_numpy(int)
    yv = (val["Y_level"] == "RESPECT").to_numpy(int)
    m = LogisticRegression(C=1.0, max_iter=10000)
    m.fit(Xd, yd)
    pl = np.clip(m.predict_proba(Xv)[:, 1], 1e-9, 1 - 1e-9)
    ph = dict(zip(cell_key(cells), cells["p_hat"]))
    pb = []
    for k in cell_key(val):
        p = ph.get(k, np.nan)
        if not np.isfinite(p):
            a, b_ = prior.get(k[0], (np.nan, np.nan))
            p = a / (a + b_) if np.isfinite(a) else 0.5
        pb.append(p)
    pb = np.clip(np.array(pb), 1e-9, 1 - 1e-9)

    def ll(p):
        return float(-np.mean(yv * np.log(p) + (1 - yv) * np.log(1 - p)))
    res = {"n_develop": int(len(dev)), "n_validate": int(len(val)), "logloss_logistic": ll(pl),
           "logloss_betabinomial": ll(pb), "logloss_constant_0.5": ll(np.full(len(yv), 0.5))}
    rk = pd.Series(pb).rank(method="first")
    bins = pd.qcut(rk, 5, labels=False)
    cal = pd.DataFrame({"bin": bins, "p_hat": pb, "y": yv}).groupby("bin").agg(n=("y", "size"), mean_p_hat=("p_hat", "mean"),
                                                                             observed_respect=("y", "mean")).reset_index()
    return res, cal


def secondary_cells(real_clock):
    d = real_clock[real_clock["Y_level"].isin(["RESPECT", "BREAK"])].copy()
    dev = d[d["split"] == "develop"]
    if len(dev) < 3:
        return pd.DataFrame()
    cuts = np.quantile(dev["speed15"].dropna(), [1 / 3, 2 / 3])
    d["speed15_tercile"] = np.digitize(d["speed15"], cuts)
    rows = []
    for t in LEVEL_TYPES:
        sub = d[(d["level_type"] == t) & (d["split"] == "develop")]
        g = sub.groupby(["box", "s", "tsib_bucket", "speed15_tercile"])["Y_level"]
        nR = g.apply(lambda y: (y == "RESPECT").sum())
        n = g.size()
        a, b_ = bb_mom(nR.to_numpy(float), n.to_numpy(float))
        for key in n.index:
            vv = d[(d["level_type"] == t) & (d["split"] == "validate") & (d["box"] == key[0]) & (d["s"] == key[1]) &
                   (d["tsib_bucket"] == key[2]) & (d["speed15_tercile"] == key[3])]
            rows.append({"level_type": t, "box": key[0], "s": key[1], "tsib_bucket": key[2], "speed15_tercile": int(key[3]),
                         "dev_nR": int(nR[key]), "dev_n": int(n[key]),
                         "dev_p_hat_pooled": (nR[key] + a) / (n[key] + a + b_) if np.isfinite(a) else np.nan,
                         "val_n": int(len(vv)), "val_share": float((vv["Y_level"] == "RESPECT").mean()) if len(vv) else np.nan})
    out = pd.DataFrame(rows)
    out.attrs["cuts"] = cuts.tolist()
    return out


def h1_placebo_diagnostic(ev, scored):
    """Diagnostic, not a pass/fail input: RESPECT share at real levels against primary placebo levels
    with the same cell key, so the label's own geometry (5 bp touch band, +-10 bp barriers) is held fixed."""
    e = ev[ev["clock_ok"] & ev["eligible"] & ev["Y_level"].isin(["RESPECT", "BREAK"]) & ev["split"].isin(scored)]
    e = e[(e["kind"] == "real") | ((e["kind"] == "pct") & ~e["placebo_dropped"])]
    rows = []
    groupings = (("all", []), ("pen_class", ["pen_class"]), ("cell", ["level_type", "box", "s", "tsib_bucket"]))
    for gname, cols in groupings:
        for keys, grp in e.groupby(["split"] + cols):
            keys = keys if isinstance(keys, tuple) else (keys,)
            r = grp[grp["kind"] == "real"]
            p = grp[grp["kind"] == "pct"]
            row = {"grouping": gname, "split": keys[0], "key": "|".join(map(str, keys[1:])) or "all",
                   "n_real": len(r), "respect_real": (r["Y_level"] == "RESPECT").mean() if len(r) else np.nan,
                   "n_placebo": len(p), "respect_placebo": (p["Y_level"] == "RESPECT").mean() if len(p) else np.nan}
            row["real_minus_placebo"] = row["respect_real"] - row["respect_placebo"]
            rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- v1.1 robustness rows


def r_oi(res, scored):
    gate, real = res["gate"], res["real"]
    rc = real[real["clock_ok"]]
    rows = []
    for sp in [s for s in scored if s != "warmup"]:
        e = rc[rc["split"] == sp]
        y = e["Y_fwd_3"]
        conf = e["confirm_RESPECT"]
        base = y[~conf].mean()
        for nm, m in (("loaded (oi_d5c > 0)", e["oi_d5c"] > 0), ("plain (oi_d5c <= 0)", e["oi_d5c"] <= 0), ("oi NA", e["oi_na"])):
            sel = y[conf & m]
            ag = gate[(gate["split"] == sp) & gate["AGREE"] & (gate["H_L"] == "RESPECT")]
            agm = ag[(ag["oi_d5c"] > 0) if nm.startswith("loaded") else ((ag["oi_d5c"] <= 0) if nm.startswith("plain") else ag["oi_na"])]
            rows.append({"split": sp, "split_by_oi": nm, "n_confirm_RESPECT": int(sel.notna().sum()),
                         "delta_real_RESPECT": sel.mean() - base, "n_AGREE_RESPECT": int(len(agm)),
                         "mean_ynet3_AGREE_RESPECT": agm["Y_net_primary"].mean() if len(agm) else np.nan})
    return pd.DataFrame(rows)


def r_regime(res, scored, h):
    real, plac, gate = res["real"], res["plac"], res["gate"]
    rows = []
    for tag in ("post_cash", "cme_break", "other"):
        flt = lambda d, tag=tag: d[(d["box"] == "UTC") & (d["regime_tag"] == tag)]  # noqa: E731
        for sp in [s for s in scored if s != "warmup"]:
            for r in h2_split(real[real["clock_ok"]], plac[plac["clock_ok"]], sp, h, flt):
                ag = gate[(gate["split"] == sp) & gate["AGREE"] & (gate["box"] == "UTC") & (gate["regime_tag"] == tag)]
                r.update({"regime_tag": tag, "n_AGREE": int(len(ag)), "mean_ynet3_AGREE": ag["Y_net_primary"].mean() if len(ag) else np.nan})
                rows.append(r)
    return pd.DataFrame(rows)


def r_stop(res, bars, scored):
    gate = res["gate"]
    ag = gate[gate["AGREE"] & gate["split"].isin(scored)].copy()
    N = bars.N
    ys, stopped, fees = [], [], []
    for r in ag.itertuples():
        g, s, L = r.g, r.s, r.L
        d = s if r.H_L == "RESPECT" else -s
        p_stop = L * (1 - s * 0.001) if r.H_L == "RESPECT" else L * (1 + s * 0.001)
        o1 = bars.O[g + 1] if g + 1 < N else np.nan
        ex, st = (bars.C[g + 3] if g + 3 < N else np.nan), False
        for j in range(g + 1, min(g + 4, N)):
            if d == 1 and bars.Lo[j] <= p_stop:
                ex, st = min(bars.O[j], p_stop), True
                break
            if d == -1 and bars.Hi[j] >= p_stop:
                ex, st = max(bars.O[j], p_stop), True
                break
        ys.append(d * np.log(ex / o1) * 1e4)
        stopped.append(st)
        fees.append(STOP_FEE[r.H_L] if st else PRIMARY_FEE[r.H_L])
    ag["Y_stop_3"] = ys
    ag["stopped"] = stopped
    ag["Y_stop_net"] = ag["Y_stop_3"] - np.array(fees)
    rows = []
    for sp in [s for s in scored if s != "warmup"]:
        e = ag[ag["split"] == sp]
        rows.append({"split": sp, "n_AGREE": int(len(e)), "mean_ynet3_no_stop": e["Y_net_primary"].mean() if len(e) else np.nan,
                     "mean_ynet3_with_stop": e["Y_stop_net"].mean() if len(e) else np.nan,
                     "stop_out_rate": e["stopped"].mean() if len(e) else np.nan})
    return pd.DataFrame(rows), ag[["event_id", "Y_stop_3", "stopped", "Y_stop_net"]]


# ----------------------------------------------------------------------------- driver


def robustness_cfgs():
    base = Cfg()
    return [
        dataclasses.replace(base, name="TI_into>=0.10", ti_thr=0.10),
        dataclasses.replace(base, name="TI_into>=0.30", ti_thr=0.30),
        dataclasses.replace(base, name="arming 10 bars", arm_k=10),
        dataclasses.replace(base, name="arming 20 bars", arm_k=20),
        dataclasses.replace(base, name="r = 5 bp", r_bp=5.0),
        dataclasses.replace(base, name="r = 20 bp", r_bp=20.0),
        dataclasses.replace(base, name="H = 15 bars", h_level=15),
        dataclasses.replace(base, name="H = 60 bars", h_level=60),
        dataclasses.replace(base, name="CAL=PROXY", cal="PROXY"),
        dataclasses.replace(base, name="clusters excluded", clusters="exclude"),
        dataclasses.replace(base, name="BOX=EXCLUSIVE", box_mode="EXCLUSIVE"),
        dataclasses.replace(base, name="UTC box only", box_mode="UTC"),
        dataclasses.replace(base, name="NY box only", box_mode="NY"),
        dataclasses.replace(base, name="sigma placebos", placebo="sigma"),
    ]


def summarize_run(res, cfg, scored):
    h1 = h1_verdict(res["cells"], scored)
    h2v = h2_verdict(res["h2"], scored)
    gs, gv = g_stats(res["gate"], scored, h1.get("PASS", False))
    row = {"run": cfg.name, "n_lean_develop": h1["n_lean_develop"], "lean_cells": h1["lean_cells"],
           "H1_PASS": h1.get("PASS"), "H2_PASS": h2v.get("PASS"), "G_PASS": gv.get("PASS")}
    for sp in [s for s in scored if s in ("validate", "test")]:
        for H in ("RESPECT", "BREAK"):
            r = res["h2"][(res["h2"]["split"] == sp) & (res["h2"]["H"] == H)]
            if len(r):
                r = r.iloc[0]
                row[f"I_{H}_{sp}"] = r["I"]
                row[f"I_{H}_{sp}_lo975"] = r["I_lo975"]
                row[f"delta_real_{H}_{sp}"] = r["delta_real"]
        a = gs[(gs["split"] == sp) & (gs["group"] == "AGREE")]
        if len(a):
            row[f"n_AGREE_{sp}"] = int(a.iloc[0]["n"])
            row[f"mean_ynet3_AGREE_{sp}"] = a.iloc[0]["mean_ynet3_primary"]
    return row


def events_out(ev, scored_written):
    keep = ["event_id", "cluster_id", "is_placebo", "kind", "offset", "offset_bp", "split", "box", "date", "open_time", "level_type",
            "instance_id", "L", "s", "tsib_bucket", "speed15", "dist_vwap_sigma", "ib_width_rel", "vwap_slope30", "touch_seq",
            "TI_t", "TI_into", "pen_t", "pen_class", "cl_t", "vz_t", "atsz_t", "oi_d5c", "oi_na", "TI_spot_t", "Y_level",
            "Y_fwd_3", "Y_fwd_5", "Y_fwd_15", "Y_fwd_30", "clock_ok", "impulse", "cal_tag", "algebra_tag", "regime_tag",
            "placebo_dropped", "min_dist_real_bp"]
    e = ev[ev["split"].isin(scored_written)]
    e = e[[c for c in keep if c in e.columns]].copy()
    e["date"] = e["date"].astype(str)
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stage", choices=["validate", "test"], required=True)
    ap.add_argument("--skip-robustness", action="store_true")
    args = ap.parse_args()
    scored = ["develop", "validate"] + (["test"] if args.stage == "test" else [])
    os.makedirs(args.out, exist_ok=True)
    b1, b5, man, metrics_days, fmt = load_all(args.data)
    cfg = Cfg()
    res = run(b1, cfg, scored)
    ev = res["events"]
    written = scored
    man.to_csv(os.path.join(args.out, "inputs_manifest.csv"), index=False)
    metrics_days.to_csv(os.path.join(args.out, "metrics_stamps_per_day.csv"), index=False)
    events_out(ev, written).to_parquet(os.path.join(args.out, "events.parquet"), index=False, compression="zstd")
    cells = res["cells"]
    cells.to_csv(os.path.join(args.out, "h1_cells.csv"), index=False)
    res["h2"].to_csv(os.path.join(args.out, "h2_interaction.csv"), index=False)
    res["edge"].to_csv(os.path.join(args.out, "edge_table.csv"), index=False)
    gate = res["gate"]
    gcols = ["event_id", "cluster_id", "cluster_members", "gate_event", "split", "box", "date", "open_time", "level_type", "instance_id",
             "cell", "H_L", "s", "L", "clock_ok", "impulse", "independent_agree", "conf_HL", "veto_HL", "liq_veto_5m",
             "cluster_conflict", "print_confirm", "depth_agree", "edge_ok", "first_fail", "AGREE", "Y_fwd_3",
             "Y_net_0.00", "Y_net_1.09", "Y_net_2.18", "Y_net_primary", "oi_d5c", "oi_na", "regime_tag"]
    gl = gate[gate["split"].isin(written)][gcols].copy()
    gl["date"] = gl["date"].astype(str)
    gl["gate_tag"] = "GATE_PARTIAL"
    gl.to_parquet(os.path.join(args.out, "gate_log.parquet"), index=False, compression="zstd")
    gate_summary(gate, written).to_csv(os.path.join(args.out, "gate_summary.csv"), index=False)
    volume_shadow(gate, written).to_csv(os.path.join(args.out, "volume_shadow.csv"), index=False)
    gs, gv = g_stats(gate, written, h1_verdict(cells, scored).get("PASS", False))
    gs.to_csv(os.path.join(args.out, "g_stats.csv"), index=False)
    real_clock = res["real"][res["real"]["clock_ok"]]
    lr, cal = logistic_check(real_clock, cells, res["prior"])
    cal.to_csv(os.path.join(args.out, "h1_calibration_validate.csv"), index=False)
    h1_placebo_diagnostic(ev, written).to_csv(os.path.join(args.out, "h1_placebo_diagnostic.csv"), index=False)
    sec = secondary_cells(real_clock)
    sec.to_csv(os.path.join(args.out, "h1_secondary_cells_exploratory.csv"), index=False)
    roi = r_oi(res, written)
    roi.to_csv(os.path.join(args.out, "r_oi.csv"), index=False)
    rreg = r_regime(res, written, cfg.h_primary)
    rreg.to_csv(os.path.join(args.out, "r_regime.csv"), index=False)
    rst, rst_ev = r_stop(res, b1, written)
    rst.to_csv(os.path.join(args.out, "r_stop.csv"), index=False)
    counts = []
    for sp in written:
        e = ev[ev["split"] == sp]
        r = e[~e["is_placebo"]]
        counts.append({"split": sp, "real_events": int(len(r)), "real_clock_ok": int(r["clock_ok"].sum()),
                       "real_in_clusters": int((r["cluster_id"] >= 0).sum()),
                       "pct_placebo_events": int((e["kind"] == "pct").sum()),
                       "pct_placebo_kept": int(((e["kind"] == "pct") & ~e["placebo_dropped"]).sum()),
                       "sigma_placebo_kept": int(((e["kind"] == "sigma") & ~e["placebo_dropped"]).sum())})
    pd.DataFrame(counts).to_csv(os.path.join(args.out, "event_counts.csv"), index=False)
    summary = {"stage": args.stage, "scored_splits": scored, "formats": fmt,
               "H1": h1_verdict(cells, scored), "H2": h2_verdict(res["h2"], scored), "G": gv,
               "logistic_check": lr, "speed15_tercile_cuts": sec.attrs.get("cuts") if len(sec) else None,
               "prior_by_type": {k: list(v) for k, v in res["prior"].items()},
               "edge_ok_cells": sorted(res["edge"].loc[res["edge"]["edge_ok"], "cell"].tolist())}
    if args.stage == "test" and not args.skip_robustness:
        rows = [summarize_run(res, cfg, scored)]
        z = res["z"]
        for rc in robustness_cfgs():
            reuse = rc.arm_k == cfg.arm_k and rc.r_bp == cfg.r_bp and rc.h_level == cfg.h_level
            if reuse and rc.cal == cfg.cal and rc.box_mode == cfg.box_mode:
                ev2 = ev.drop(columns=[c for c in ev.columns if c.startswith(("confirm_", "veto_", "liq_veto"))])
                r2 = run(b1, rc, scored, events=ev2)
            else:
                r2 = run(b1, rc, scored, z_v=z[0], z_ats=z[1])
            rows.append(summarize_run(r2, rc, scored))
            print("robustness done:", rc.name, flush=True)
        c5 = Cfg(name="5 m bars (arming 3, H = 6, Y_fwd h = 1 bar)", bar_min=5, arm_k=3, h_level=6, h_fwd=(1, 3, 6), h_primary=1)
        r5 = run(b5, c5, scored)
        rows.append(summarize_run(r5, c5, scored))
        r5["cells"].to_csv(os.path.join(args.out, "robust_5m_h1_cells.csv"), index=False)
        pd.DataFrame(rows).to_csv(os.path.join(args.out, "robustness.csv"), index=False)
    with open(os.path.join(args.out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(json.dumps({k: summary[k] for k in ("H1", "H2", "G")}, indent=2, default=str))


if __name__ == "__main__":
    main()
