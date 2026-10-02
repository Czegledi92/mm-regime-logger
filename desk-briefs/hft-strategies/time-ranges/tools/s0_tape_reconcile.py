"""S0-lite tape reconciliation for the BTC perp time-range study. PAPER / RESEARCH ONLY.

Descriptive only, on a handful of days from the public Binance archive:

1. Daily 1m klines against 1m bars rebuilt from raw ``trades`` and from ``aggTrades``.
2. 1s bars from ``aggTrades`` against 1s bars from raw ``trades`` (aggTrade timestamps are the first
   fill's time, so members can sit in a later second).
3. Trade-id continuity in the raw ``trades`` file.
4. For every zero-trade run found in the monthly 1m klines: monthly vs daily klines, and prints in the
   aggTrades tape inside the run.

No range label, break, reversal or continuation rate, or forward return is computed.

    python3 desk-briefs/hft-strategies/time-ranges/tools/s0_tape_reconcile.py [--cache DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s0_archive_audit as A  # noqa: E402

RECON_DAYS = ["2020-01-01", "2023-11-10", "2026-09-01"]
AGG_COLS = ["agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id", "transact_time", "is_buyer_maker"]
TRADE_COLS = ["id", "price", "qty", "quote_qty", "time", "is_buyer_maker"]


def daily(kind: str, day: str, cache: Path) -> pd.DataFrame:
    """kind is 'klines_1m', 'trades' or 'aggTrades'."""
    if kind == "klines_1m":
        key, cols = f"data/futures/um/daily/klines/BTCUSDT/1m/BTCUSDT-1m-{day}.zip", A.KLINE_COLS
    else:
        key = f"data/futures/um/daily/{kind}/BTCUSDT/BTCUSDT-{kind}-{day}.zip"
        cols = AGG_COLS if kind == "aggTrades" else TRADE_COLS
    df, _, _ = A.read_zip_csv(A.fetch(key, cache))
    df = df.iloc[:, : len(cols)]
    df.columns = cols
    return df


def ohlcv(t_ms: np.ndarray, px: np.ndarray, qty: np.ndarray, bar_ms: int) -> pd.DataFrame:
    df = pd.DataFrame({"k": t_ms // bar_ms * bar_ms, "p": px, "q": qty})
    return df.groupby("k").agg(o=("p", "first"), h=("p", "max"), l=("p", "min"), c=("p", "last"), v=("q", "sum"), n=("p", "size"))


def mismatches(x: pd.DataFrame, y: pd.DataFrame) -> dict:
    j = x.join(y, how="outer", lsuffix="_x", rsuffix="_y")
    present = j["o_x"].notna() & j["o_y"].notna()
    hl = present & ~(np.isclose(j["h_x"], j["h_y"]) & np.isclose(j["l_x"], j["l_y"]))
    oc = present & ~(np.isclose(j["o_x"], j["o_y"]) & np.isclose(j["c_x"], j["c_y"]))
    vol = present & ~np.isclose(j["v_x"], j["v_y"], atol=1e-6)
    return {"bars_compared": int(present.sum()), "bars_only_in_one": int((~present).sum()),
            "high_or_low_differs": int(hl.sum()), "open_or_close_differs": int(oc.sum()), "volume_differs": int(vol.sum())}


def reconcile_day(day: str, cache: Path) -> dict:
    k = daily("klines_1m", day, cache)
    t = daily("trades", day, cache)
    a = daily("aggTrades", day, cache)
    kb = k.set_index(k["open_time"].astype("int64"))[["open", "high", "low", "close", "volume", "count"]]
    kb.columns = ["o", "h", "l", "c", "v", "n"]

    t_ms, a_ms = t["time"].astype("int64").values, a["transact_time"].astype("int64").values
    trade_1m = ohlcv(t_ms, t["price"].values, t["qty"].values, 60_000)
    agg_1m = ohlcv(a_ms, a["price"].values, a["quantity"].values, 60_000)
    trade_1s = ohlcv(t_ms, t["price"].values, t["qty"].values, 1_000)
    agg_1s = ohlcv(a_ms, a["price"].values, a["quantity"].values, 1_000)

    idx = np.searchsorted(a["first_trade_id"].values, t["id"].values, side="right") - 1
    mapped = (idx >= 0) & (t["id"].values <= a["last_trade_id"].values[np.clip(idx, 0, None)])
    lag = t_ms - a_ms[np.clip(idx, 0, None)]
    ids = t["id"].values
    return {
        "day": day,
        "trades_rows": int(len(t)), "aggtrades_rows": int(len(a)),
        "trades_mapped_to_an_aggtrade": int(mapped.sum()),
        "trade_time_minus_aggtrade_time_ms_max": int(lag[mapped].max()),
        "trades_in_later_second_than_their_aggtrade": int(((t_ms // 1000) != (a_ms[np.clip(idx, 0, None)] // 1000))[mapped].sum()),
        "trades_in_later_minute_than_their_aggtrade": int(((t_ms // 60_000) != (a_ms[np.clip(idx, 0, None)] // 60_000))[mapped].sum()),
        "trade_id_span": int(ids.max() - ids.min() + 1), "trade_ids_absent_from_trades_file": int(ids.max() - ids.min() + 1 - len(ids)),
        "kline_count_sum": int(kb["n"].sum()),
        **{f"kline_vs_trades_1m_{kk}": vv for kk, vv in mismatches(kb, trade_1m).items()},
        **{f"kline_vs_aggtrades_1m_{kk}": vv for kk, vv in mismatches(kb, agg_1m).items()},
        **{f"trades_vs_aggtrades_1s_{kk}": vv for kk, vv in mismatches(trade_1s, agg_1s).items()},
    }


def zero_runs(cache: Path) -> pd.DataFrame:
    bars, _ = A.load_um_1m(cache)
    z = np.sort(bars.loc[bars["count"] == 0, "open_time"].astype("int64").values)
    if not len(z):
        return pd.DataFrame()
    brk = np.where(np.diff(z) != 60_000)[0]
    starts, ends = np.r_[z[0], z[brk + 1]], np.r_[z[brk], z[-1]] + 60_000
    rows = []
    for s, e in zip(starts, ends):
        day = pd.to_datetime(s, unit="ms", utc=True).strftime("%Y-%m-%d")
        d = daily("klines_1m", day, cache)
        d = d[(d["open_time"] >= s) & (d["open_time"] < e)]
        a = daily("aggTrades", day, cache)
        at = a["transact_time"].astype("int64").values
        t = daily("trades", day, cache)
        tt = t["time"].astype("int64").values
        in_agg = int(((at >= s) & (at < e)).sum())
        in_trades = int(((tt >= s) & (tt < e)).sum())
        in_daily = int(d["count"].sum())
        if in_daily == 0 and in_agg == 0 and in_trades == 0:
            verdict = "no prints in any public source"
        elif in_daily > 0:
            verdict = "monthly kline defect: daily klines and tape have prints"
        else:
            verdict = "kline defect (monthly and daily): tape has prints"
        rows.append({
            "run_start_utc": pd.to_datetime(s, unit="ms", utc=True).isoformat(),
            "run_end_utc": pd.to_datetime(e, unit="ms", utc=True).isoformat(),
            "minutes": int((e - s) // 60_000),
            "daily_kline_trades_in_run": in_daily,
            "raw_trades_in_run": in_trades,
            "aggtrades_rows_in_run": in_agg,
            "verdict": verdict,
        })
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/tr-archive")
    cache = Path(ap.parse_args().cache)
    days = pd.DataFrame([reconcile_day(d, cache) for d in RECON_DAYS])
    days.to_csv(A.RESULTS / "s0_tape_reconcile_days.csv", index=False)
    runs = zero_runs(cache)
    runs.to_csv(A.RESULTS / "s0_um_1m_zero_trade_runs_vs_tape.csv", index=False)
    out = {"days": days.to_dict(orient="records"), "zero_trade_runs": runs.to_dict(orient="records")}
    (A.RESULTS / "s0_tape_reconcile.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
