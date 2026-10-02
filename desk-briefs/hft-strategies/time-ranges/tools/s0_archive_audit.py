"""S0-lite archive audit for the BTC perp time-range study. PAPER / RESEARCH ONLY.

Descriptive only. This script computes coverage, gaps, clocks and volume seasonality from the public
Binance archive (data.binance.vision). It computes no range label, no break, no reversal or
continuation rate, and no forward return. Raw data is cached outside the repo (default /tmp/tr-archive).

    python3 desk-briefs/hft-strategies/time-ranges/tools/s0_archive_audit.py [--cache DIR]

Writes small CSV/JSON files to ../results/ and one figure to ../figures/.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import io
import json
import re
import urllib.parse
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

LIST_URL = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
FILE_URL = "https://data.binance.vision"
HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "results"
FIGURES = HERE.parent / "figures"

UM_1M = "data/futures/um/monthly/klines/BTCUSDT/1m/"
UM_FUNDING = "data/futures/um/monthly/fundingRate/BTCUSDT/"
UM_AGGTRADES = "data/futures/um/monthly/aggTrades/BTCUSDT/"
UM_TRADES = "data/futures/um/monthly/trades/BTCUSDT/"
SPOT_1S = "data/spot/monthly/klines/BTCUSDT/1s/"

KLINE_COLS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore",
]
NY = ZoneInfo("America/New_York")
LDN = ZoneInfo("Europe/London")


def list_prefix(prefix: str) -> list[tuple[str, int]]:
    out, marker = [], ""
    while True:
        url = f"{LIST_URL}?delimiter=/&prefix={urllib.parse.quote(prefix)}"
        if marker:
            url += f"&marker={urllib.parse.quote(marker)}"
        xml = urllib.request.urlopen(url, timeout=60).read().decode()
        keys = re.findall(r"<Key>([^<]+)</Key>", xml)
        sizes = [int(s) for s in re.findall(r"<Size>([^<]+)</Size>", xml)]
        out += list(zip(keys, sizes))
        if "<IsTruncated>true" in xml and keys:
            marker = keys[-1]
        else:
            return out


def monthly_zips(prefix: str) -> list[tuple[str, int]]:
    """Archive monthly files named <SYMBOL>-<kind>-YYYY-MM.zip (stray part-*.zip files are ignored)."""
    return [(k, s) for k, s in list_prefix(prefix) if re.search(r"-\d{4}-\d{2}\.zip$", k)]


def fetch(key: str, cache: Path) -> Path:
    dest = cache / key
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    blob = urllib.request.urlopen(f"{FILE_URL}/{key}", timeout=300).read()
    expected = urllib.request.urlopen(f"{FILE_URL}/{key}.CHECKSUM", timeout=60).read().decode().split()[0]
    got = hashlib.sha256(blob).hexdigest()
    if got != expected:
        raise ValueError(f"checksum mismatch for {key}: {got} != {expected}")
    dest.write_bytes(blob)
    return dest


def read_zip_csv(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as z:
        raw = z.read(z.namelist()[0]).decode()
    has_header = not raw[:1].isdigit()
    return pd.read_csv(io.StringIO(raw), header=0 if has_header else None), has_header, raw


def load_um_1m(cache: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    files = monthly_zips(UM_1M)
    with cf.ThreadPoolExecutor(8) as ex:
        paths = list(ex.map(lambda kv: fetch(kv[0], cache), files))
    frames, meta = [], []
    for (key, size), path in zip(files, paths):
        df, has_header, raw = read_zip_csv(path)
        df.columns = KLINE_COLS
        month = re.search(r"(\d{4}-\d{2})\.zip$", key).group(1)
        prices = re.findall(r"^\d+,([\d.]+),([\d.]+),([\d.]+),([\d.]+),", raw, flags=re.M)
        flat = [p for row in prices for p in row]
        decimals = max(len(p.split(".")[1]) if "." in p else 0 for p in flat)
        second_decimal_used = any(len(p.split(".")[1]) >= 2 and p.split(".")[1][1] != "0" for p in flat if "." in p)
        meta.append({
            "month": month, "zip_bytes": size, "rows": len(df), "header_row": has_header,
            "max_price_decimals": decimals, "second_decimal_nonzero": second_decimal_used,
            "ts_digits": len(str(int(df["open_time"].iloc[0]))),
        })
        frames.append(df)
    bars = pd.concat(frames, ignore_index=True)
    return bars, pd.DataFrame(meta)


def gap_audit(bars: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    t = bars["open_time"].astype("int64")
    dup = int(t.duplicated().sum())
    t = np.sort(t.unique())
    step = 60_000
    off_grid = int((t % step != 0).sum())
    start, end = int(t[0]), int(t[-1])
    expected = np.arange(start, end + step, step)
    missing = np.setdiff1d(expected, t)
    miss_dt = pd.to_datetime(missing, unit="ms", utc=True)
    exp_dt = pd.to_datetime(expected, unit="ms", utc=True)
    per_year = pd.DataFrame({
        "expected_minutes": pd.Series(exp_dt.year).value_counts().sort_index(),
        "missing_minutes": pd.Series(miss_dt.year).value_counts().sort_index(),
    }).fillna(0).astype(int)
    per_year["missing_pct"] = (100 * per_year["missing_minutes"] / per_year["expected_minutes"]).round(4)
    zero_trade = bars[bars["count"] == 0]
    per_year["zero_trade_minutes"] = (
        pd.to_datetime(zero_trade["open_time"], unit="ms", utc=True).dt.year.value_counts()
        .reindex(per_year.index).fillna(0).astype(int)
    )
    gap_days = pd.Series(miss_dt.normalize().unique())
    per_year["utc_days_with_any_missing_minute"] = gap_days.dt.year.value_counts().reindex(per_year.index).fillna(0).astype(int)

    runs = []
    if len(missing):
        brk = np.where(np.diff(missing) != step)[0]
        starts = np.r_[missing[0], missing[brk + 1]]
        ends = np.r_[missing[brk], missing[-1]]
        for s, e in zip(starts, ends):
            runs.append({
                "gap_start_utc": pd.to_datetime(s, unit="ms", utc=True).isoformat(),
                "gap_end_utc": pd.to_datetime(e + step, unit="ms", utc=True).isoformat(),
                "missing_minutes": int((e - s) // step + 1),
            })
    gaps = pd.DataFrame(runs, columns=["gap_start_utc", "gap_end_utc", "missing_minutes"])
    summary = {
        "first_bar_utc": pd.to_datetime(start, unit="ms", utc=True).isoformat(),
        "last_bar_utc": pd.to_datetime(end, unit="ms", utc=True).isoformat(),
        "rows": int(len(bars)), "duplicate_open_times": dup, "off_grid_open_times": off_grid,
        "missing_minutes_total": int(len(missing)), "gap_runs": int(len(runs)),
        "gap_runs_ge_5min": int((gaps["missing_minutes"] >= 5).sum()) if len(gaps) else 0,
        "longest_gap_minutes": int(gaps["missing_minutes"].max()) if len(gaps) else 0,
        "zero_trade_minutes_total": int(len(zero_trade)),
    }
    return per_year.reset_index(names="year"), gaps, summary


def funding_audit(cache: Path) -> tuple[pd.DataFrame, dict]:
    files = monthly_zips(UM_FUNDING)
    with cf.ThreadPoolExecutor(8) as ex:
        paths = list(ex.map(lambda kv: fetch(kv[0], cache), files))
    rows = []
    for path in paths:
        df, has_header, _ = read_zip_csv(path)
        df = df.iloc[:, :3]
        df.columns = ["calc_time", "funding_interval_hours", "last_funding_rate"]
        rows.append(df)
    f = pd.concat(rows, ignore_index=True)
    ts = pd.to_datetime(f["calc_time"].astype("int64"), unit="ms", utc=True)
    f["hour_utc"] = ts.dt.hour
    f["minute_utc"] = ts.dt.minute
    f["month"] = ts.dt.strftime("%Y-%m")
    by_month = f.groupby("month").agg(
        events=("calc_time", "size"),
        interval_hours_set=("funding_interval_hours", lambda s: ",".join(map(str, sorted(set(s))))),
        hours_utc_set=("hour_utc", lambda s: ",".join(map(str, sorted(set(s))))),
    ).reset_index()
    summary = {
        "first_event_utc": ts.min().isoformat(), "last_event_utc": ts.max().isoformat(),
        "events": int(len(f)),
        "interval_hours_values": sorted(int(x) for x in set(f["funding_interval_hours"])),
        "hours_utc_values": sorted(int(x) for x in set(f["hour_utc"])),
        "events_not_on_minute_00": int((f["minute_utc"] != 0).sum()),
        "max_calc_time_offset_ms_past_the_hour": int((f["calc_time"].astype("int64") % 3_600_000).max()),
    }
    return by_month, summary


def dst_calendar(y0: int = 2018, y1: int = 2026) -> pd.DataFrame:
    """Daily UTC offsets for New York and London; returns the US/UK transition dates and mismatch spans."""
    out = []
    for y in range(y0, y1 + 1):
        days = [date(y, 1, 1) + timedelta(d) for d in range((date(y + 1, 1, 1) - date(y, 1, 1)).days)]

        def off(tz, d):
            return datetime(d.year, d.month, d.day, 12, tzinfo=timezone.utc).astimezone(tz).utcoffset()

        ny = [off(NY, d) for d in days]
        ld = [off(LDN, d) for d in days]
        us_on = [d for d, o in zip(days, ny) if o == timedelta(hours=-4)]
        uk_on = [d for d, o in zip(days, ld) if o == timedelta(hours=1)]
        gap = [d for d, a, b in zip(days, ny, ld) if (b - a) != timedelta(hours=5)]
        spans, cur = [], []
        for d in gap:
            if cur and (d - cur[-1]).days != 1:
                spans.append(cur)
                cur = []
            cur.append(d)
        if cur:
            spans.append(cur)
        out.append({
            "year": y,
            "us_edt_first_day": us_on[0].isoformat(), "us_edt_last_day": us_on[-1].isoformat(),
            "uk_bst_first_day": uk_on[0].isoformat(), "uk_bst_last_day": uk_on[-1].isoformat(),
            "london_ny_4h_spans": "; ".join(f"{s[0].isoformat()}..{s[-1].isoformat()} ({len(s)}d)" for s in spans),
            "london_ny_4h_days": len(gap),
        })
    return pd.DataFrame(out)


def volume_by_clock(bars: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    ts = pd.to_datetime(bars["open_time"].astype("int64"), unit="ms", utc=True)
    df = pd.DataFrame({"ts": ts, "vol": bars["volume"].astype(float)})
    df["date"] = df["ts"].dt.date
    df["dow"] = df["ts"].dt.dayofweek
    df["bucket"] = (df["ts"].dt.hour * 60 + df["ts"].dt.minute) // 5
    noon = pd.to_datetime(df["date"].astype(str) + " 12:00").dt.tz_localize("UTC")
    df["ny_dst"] = noon.dt.tz_convert(NY).map(lambda x: x.utcoffset() == timedelta(hours=-4))
    day_tot = df.groupby("date")["vol"].transform("sum")
    df["share"] = df["vol"] / day_tot
    wk = df[df["dow"] < 5]
    per_day = wk.groupby(["date", "ny_dst", "bucket"], as_index=False)["share"].sum()
    prof = (per_day.groupby(["ny_dst", "bucket"])["share"].mean().unstack(0) * 100)
    prof = prof.rename(columns={False: "us_standard_time_pct", True: "us_daylight_time_pct"})
    prof = prof[["us_standard_time_pct", "us_daylight_time_pct"]]
    prof.index = [f"{b * 5 // 60:02d}:{b * 5 % 60:02d}" for b in prof.index]
    prof.index.name = "utc_bucket_start"
    days = wk.groupby("ny_dst")["date"].nunique()

    steps = {}
    for col in prof.columns:
        s = prof[col]
        jump = (s - s.shift(1)).iloc[1:]
        top = jump.sort_values(ascending=False).head(4)
        steps[col] = [{"utc_bucket": k, "share_step_pct_points": round(float(v), 4), "share_pct": round(float(s[k]), 4)} for k, v in top.items()]

    daily = df.groupby("date").agg(vol=("vol", "sum"), dow=("dow", "first")).reset_index()
    daily["year"] = pd.to_datetime(daily["date"]).dt.year
    daily["weekend"] = daily["dow"] >= 5
    ww = daily.groupby(["year", "weekend"])["vol"].median().unstack()
    ww.columns = ["median_weekday_btc", "median_weekend_btc"]
    ww["weekend_over_weekday"] = (ww["median_weekend_btc"] / ww["median_weekday_btc"]).round(3)
    summary = {
        "weekdays_us_standard_time": int(days.get(False, 0)),
        "weekdays_us_daylight_time": int(days.get(True, 0)),
        "largest_5m_share_steps": steps,
    }
    return prof.round(5).reset_index(), ww.round(1).reset_index(), summary


def session_counts() -> pd.DataFrame:
    splits = {
        "launch_trades_only": (date(2019, 9, 8), date(2019, 12, 31)),
        "develop": (date(2020, 1, 1), date(2023, 12, 31)),
        "validate": (date(2024, 1, 1), date(2025, 6, 30)),
        "test_touch_once": (date(2025, 7, 1), date(2026, 9, 30)),
        "perp_primary_total": (date(2020, 1, 1), date(2026, 9, 30)),
        "spot_control_2018_2019": (date(2018, 1, 1), date(2019, 12, 31)),
    }
    rows = []
    for name, (a, b) in splits.items():
        n = (b - a).days + 1
        wd = sum(1 for i in range(n) if (a + timedelta(i)).weekday() < 5)
        rows.append({"split": name, "first_utc_day": a.isoformat(), "last_utc_day": b.isoformat(),
                     "calendar_days": n, "mon_fri_days": wd, "sat_sun_days": n - wd})
    return pd.DataFrame(rows)


def archive_sizes() -> pd.DataFrame:
    rows = []
    for name, prefix in [("um_aggTrades", UM_AGGTRADES), ("um_trades", UM_TRADES), ("um_klines_1m", UM_1M), ("spot_klines_1s", SPOT_1S)]:
        for key, size in monthly_zips(prefix):
            month = re.search(r"(\d{4}-\d{2})\.zip$", key).group(1)
            rows.append({"dataset": name, "year": int(month[:4]), "month": month, "zip_bytes": size})
    df = pd.DataFrame(rows)
    agg = df.groupby(["dataset", "year"]).agg(months=("month", "size"), first_month=("month", "min"),
                                              last_month=("month", "max"), zip_gb=("zip_bytes", "sum")).reset_index()
    agg["zip_gb"] = (agg["zip_gb"] / 1e9).round(2)
    return agg


def sample_checks(cache: Path) -> dict:
    """Single-day samples: timestamp units, empty-second encoding, aggTrades id continuity."""
    out = {}
    for label, key in [
        ("spot_1s_2018-03-01", "data/spot/daily/klines/BTCUSDT/1s/BTCUSDT-1s-2018-03-01.zip"),
        ("spot_1s_2026-09-01", "data/spot/daily/klines/BTCUSDT/1s/BTCUSDT-1s-2026-09-01.zip"),
    ]:
        df, has_header, _ = read_zip_csv(fetch(key, cache))
        df.columns = KLINE_COLS
        out[label] = {
            "rows": int(len(df)), "ts_digits": len(str(int(df["open_time"].iloc[0]))),
            "seconds_with_count_0": int((df["count"] == 0).sum()),
            "pct_seconds_with_trades": round(100 * float((df["count"] > 0).mean()), 2),
            "count_0_rows_have_flat_ohlc": bool(((df["count"] == 0) <= ((df["high"] == df["low"]) & (df["open"] == df["close"]))).all()),
        }
    for label, key in [
        ("um_aggTrades_2020-01-01", "data/futures/um/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2020-01-01.zip"),
        ("um_aggTrades_2026-09-01", "data/futures/um/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2026-09-01.zip"),
    ]:
        df, has_header, _ = read_zip_csv(fetch(key, cache))
        df = df.iloc[:, :7]
        df.columns = ["agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id", "transact_time", "is_buyer_maker"]
        sec = df["transact_time"].astype("int64") // 1000
        day0 = int(sec.min() // 86400 * 86400)
        out[label] = {
            "header_row": has_header, "rows": int(len(df)),
            "ts_digits": len(str(int(df["transact_time"].iloc[0]))),
            "agg_id_contiguous": bool((df["agg_trade_id"].diff().iloc[1:] == 1).all()),
            "trade_id_contiguous": bool((df["first_trade_id"].iloc[1:].values == df["last_trade_id"].iloc[:-1].values + 1).all()),
            "time_nondecreasing_in_id_order": bool((df["transact_time"].diff().iloc[1:] >= 0).all()),
            "pct_utc_seconds_with_trades": round(100 * sec.nunique() / 86400, 2),
            "max_seconds_without_trade": int(np.diff(np.r_[day0 - 1, np.sort(sec.unique()), day0 + 86400]).max() - 1),
            "same_ms_groups_spanning_2plus_prices": int(df.groupby(["transact_time", "is_buyer_maker"])["price"].nunique().gt(1).sum()),
        }
    tr, _, _ = read_zip_csv(fetch("data/futures/um/daily/trades/BTCUSDT/BTCUSDT-trades-2019-09-08.zip", cache))
    out["um_trades_2019-09-08"] = {"rows": int(len(tr)), "first_trade_utc": pd.to_datetime(int(tr.iloc[0, 4]), unit="ms", utc=True).isoformat()}
    return out


def plot_profile(prof: pd.DataFrame, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = np.arange(len(prof))
    buckets = list(prof["utc_bucket_start"])
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.plot(x, prof["us_standard_time_pct"], label="US standard time (EST, UTC-5) weekdays", lw=1.3)
    ax.plot(x, prof["us_daylight_time_pct"], label="US daylight time (EDT, UTC-4) weekdays", lw=1.3)
    ax.axhline(100 / 288, color="black", lw=0.6, ls=":", label="uniform share (100/288 %)")
    for hhmm in ("00:00", "08:00", "16:00"):
        ax.axvline(buckets.index(hhmm), color="tab:green", lw=0.8, alpha=0.6)
    ax.text(buckets.index("08:00") + 1, 0.12, "funding stamps 00/08/16 UTC (green)", fontsize=7, color="tab:green")
    for hhmm, txt, y in [("12:30", "08:30 ET in EDT", 0.95), ("13:30", "09:30 ET in EDT = 08:30 ET in EST", 1.01), ("14:30", "09:30 ET in EST", 0.95)]:
        i = buckets.index(hhmm)
        ax.axvline(i, color="grey", lw=0.6, ls="--")
        ax.text(i + 0.6, y, txt, fontsize=7, va="top")
    ax.set_ylim(0.1, 1.05)
    ticks = list(range(0, len(prof), 12))
    ax.set_xticks(ticks, [prof["utc_bucket_start"].iloc[i] for i in ticks])
    ax.set_xlabel("UTC time (5-minute buckets)")
    ax.set_ylabel("Mean share of the UTC day's volume (%)")
    ax.set_title("Binance USD-M BTCUSDT perp, public 1m klines 2020-01..2026-09, Mon-Fri UTC days. Descriptive, not an outcome", fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/tr-archive")
    args = ap.parse_args()
    cache = Path(args.cache)
    RESULTS.mkdir(parents=True, exist_ok=True)
    checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    bars, kline_meta = load_um_1m(cache)
    kline_meta.to_csv(RESULTS / "s0_um_1m_monthly_files.csv", index=False)
    per_year, gaps, gap_summary = gap_audit(bars)
    per_year.to_csv(RESULTS / "s0_um_1m_coverage_by_year.csv", index=False)
    gaps.to_csv(RESULTS / "s0_um_1m_gap_runs.csv", index=False)

    funding_by_month, funding_summary = funding_audit(cache)
    funding_by_month.to_csv(RESULTS / "s0_um_funding_clock_by_month.csv", index=False)

    dst = dst_calendar()
    dst.to_csv(RESULTS / "s0_dst_calendar_2018_2026.csv", index=False)

    prof, weekend, vol_summary = volume_by_clock(bars)
    prof.to_csv(RESULTS / "s0_um_volume_share_by_utc_5m_edt_vs_est.csv", index=False)
    weekend.to_csv(RESULTS / "s0_um_weekend_vs_weekday_volume_by_year.csv", index=False)
    plot_profile(prof, FIGURES / "fig01_volume_share_by_utc_clock_edt_vs_est.png")

    counts = session_counts()
    counts.to_csv(RESULTS / "s0_session_counts_by_split.csv", index=False)
    sizes = archive_sizes()
    sizes.to_csv(RESULTS / "s0_archive_sizes_by_year.csv", index=False)
    samples = sample_checks(cache)

    tick = kline_meta.loc[kline_meta["second_decimal_nonzero"], "month"]
    summary = {
        "checked_at_utc": checked_at,
        "source": "data.binance.vision public archive; sha256 CHECKSUM verified for every downloaded zip",
        "scope_note": "Descriptive audit only. No range labels, breaks, reversal/continuation rates or forward returns were computed.",
        "um_1m": gap_summary | {
            "months": int(len(kline_meta)),
            "months_with_header_row": int(kline_meta["header_row"].sum()),
            "first_month_with_header_row": kline_meta.loc[kline_meta["header_row"], "month"].min(),
            "last_month_with_two_decimal_prices_used": tick.max() if len(tick) else None,
        },
        "um_funding": funding_summary,
        "volume_by_clock": vol_summary,
        "samples": samples,
    }
    (RESULTS / "s0_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
