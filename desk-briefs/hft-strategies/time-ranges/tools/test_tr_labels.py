"""Checks for the TR label algebra v0 on synthetic paths only. No market data.

    python3 desk-briefs/hft-strategies/time-ranges/tools/test_tr_labels.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tr_labels import (  # noqa: E402
    AMBIG, CONTINUATION, NO_BREAK, REVERSAL, UNRESOLVED, Bars, Box, bars_from_ticks, label_bars, label_path,
)

BOX = Box(high=101.0, low=99.0)
T1 = 999_999_960_000
SEC = 1000


def path(*prices, step_ms=SEC):
    px = np.asarray(prices, dtype=float)
    return T1 + step_ms * np.arange(len(px)), px


def bps(x):
    return 1e4 * x / BOX.mid


def test_box_geometry():
    assert BOX.mid == 100.0
    assert math.isclose(BOX.size_bps, 200.0)


def test_no_break_and_touch_is_not_a_break():
    ts, px = path(100, 101.0, 99.0, 100.5)
    assert label_path(ts, px, BOX, T1 + 10 * SEC).outcome == NO_BREAK


def test_clean_run_is_continuation_with_negative_heat():
    ts, px = path(100, 101.2, 101.5, 102.0, 102.4)
    lab = label_path(ts, px, BOX, T1 + 10 * SEC)
    assert lab.outcome == CONTINUATION and lab.side == 1
    assert lab.t_break == T1 + SEC
    assert math.isclose(lab.heat_bps, -bps(0.2))
    assert math.isclose(lab.ife_bps, bps(0.2))
    assert math.isclose(lab.mfe_bps, bps(1.4))


def test_pullback_inside_range_then_new_high_is_continuation():
    ts, px = path(100, 101.5, 102.0, 100.5, 101.2, 102.5)
    lab = label_path(ts, px, BOX, T1 + 10 * SEC)
    assert lab.outcome == CONTINUATION
    assert math.isclose(lab.ife_bps, bps(1.0))
    assert math.isclose(lab.heat_bps, bps(0.5))
    assert math.isclose(lab.pullback_bps, bps(1.5))
    assert math.isclose(lab.mfe_bps, bps(1.5))
    assert lab.t_heat == T1 + 3 * SEC and lab.t_mfe == T1 + 5 * SEC


def test_push_pullback_no_new_extreme_is_unresolved():
    ts, px = path(100, 101.5, 102.0, 100.5, 101.9, 100.2)
    lab = label_path(ts, px, BOX, T1 + 10 * SEC)
    assert lab.outcome == UNRESOLVED
    assert math.isclose(lab.ife_bps, lab.mfe_bps)


def test_continuation_needs_new_extreme_after_last_visit_of_deepest_low():
    ts, px = path(100, 101.5, 100.5, 102.0, 100.5, 101.8)
    assert label_path(ts, px, BOX, T1 + 10 * SEC).outcome == UNRESOLVED


def test_reversal_extension_and_reversal_leg():
    ts, px = path(100, 101.3, 101.8, 100.0, 98.6, 99.4, 98.0)
    lab = label_path(ts, px, BOX, T1 + 10 * SEC)
    assert lab.outcome == REVERSAL and lab.side == 1
    assert lab.t_reversal == T1 + 4 * SEC
    assert math.isclose(lab.ext_bps, bps(0.8))
    assert math.isclose(lab.rev_ife_bps, bps(0.4))
    assert math.isclose(lab.rev_heat_bps, bps(0.4))
    assert math.isclose(lab.rev_mfe_bps, bps(1.0))
    assert math.isnan(lab.ife_bps)


def test_down_break_mirror():
    ts, px = path(100, 98.5, 98.0, 99.5, 98.8, 97.5)
    lab = label_path(ts, px, BOX, T1 + 10 * SEC)
    assert lab.outcome == CONTINUATION and lab.side == -1
    assert math.isclose(lab.heat_bps, bps(0.5))
    assert math.isclose(lab.mfe_bps, bps(1.5))


def test_window_end_is_exclusive_and_markout_reads_past_it():
    ts, px = path(100, 100.5, 101.5, 103.0)
    lab = label_path(ts, px, BOX, T1 + 2 * SEC)
    assert lab.outcome == NO_BREAK
    lab = label_path(ts, px, BOX, T1 + 3 * SEC)
    assert lab.outcome == UNRESOLVED and lab.t_break == T1 + 2 * SEC
    assert math.isclose(lab.ret_end_bps, 0.0)
    assert math.isclose(lab.ret_180s_bps, bps(1.5))


def test_double_break_inside_one_second():
    ts = T1 + np.array([0, 200, 400, 600, 2000])
    px_up_first = np.array([100.0, 101.4, 98.7, 100.0, 100.0])
    px_dn_first = np.array([100.0, 98.7, 101.4, 100.0, 100.0])
    bars = bars_from_ticks(ts, px_up_first, SEC)
    assert label_bars(bars, BOX, T1 + 5 * SEC).outcome == AMBIG

    for px, side in ((px_up_first, 1), (px_dn_first, -1)):
        bars = bars_from_ticks(ts, px, SEC)

        def ticks(t_open, ts=ts, px=px):
            m = (ts >= t_open) & (ts < t_open + SEC)
            return ts[m], px[m]

        lab = label_bars(bars, BOX, T1 + 5 * SEC, ticks)
        assert lab.outcome == REVERSAL and lab.side == side and lab.resolution == "tick"
        assert _same(lab, label_path(ts, px, BOX, T1 + 5 * SEC))


def test_zero_count_bars_are_not_prints():
    bars = Bars(
        t_open=T1 + SEC * np.arange(3), o=np.array([100.0, 102.0, 100.0]), h=np.array([100.0, 102.0, 100.0]),
        l=np.array([100.0, 102.0, 100.0]), c=np.array([100.0, 102.0, 100.0]), count=np.array([1, 0, 1]), bar_ms=SEC,
    )
    assert label_bars(bars, BOX, T1 + 3 * SEC).outcome == NO_BREAK


def _random_ticks(rng, n, t1):
    gaps = rng.exponential(250.0, n).astype(np.int64) + 1
    ts = t1 + np.cumsum(gaps)
    steps = rng.choice([-1, 0, 1], size=n, p=[0.45, 0.10, 0.45])
    px = 1000.0 + 0.1 * np.cumsum(steps)
    return ts, np.round(px, 1)


def _same(a, b):
    fields = ("outcome", "side", "t_break", "t_reversal", "t_ife", "t_heat", "t_mfe", "t_ext", "t_rev_heat", "t_rev_mfe")
    vals = ("ife_bps", "heat_bps", "pullback_bps", "mfe_bps", "ext_bps", "rev_ife_bps", "rev_heat_bps",
            "rev_pullback_bps", "rev_mfe_bps", "ret_180s_bps", "ret_end_bps")
    if any(getattr(a, f) != getattr(b, f) for f in fields):
        return False
    return all((math.isnan(getattr(a, v)) and math.isnan(getattr(b, v))) or math.isclose(getattr(a, v), getattr(b, v), abs_tol=1e-9) for v in vals)


def test_bars_with_drilldown_equal_ticks():
    """Synthetic random walks: bar labels with drill-down must equal tick labels exactly.

    The returned counts describe this synthetic generator only. They are not BTC statistics.
    """
    rng = np.random.default_rng(20261003)
    counts = {"cases": 0, "1s_ambig": 0, "1m_ambig": 0, "1s_wrong_without_ticks": 0, "1m_wrong_without_ticks": 0}
    for _ in range(300):
        t0 = T1
        ts, px = _random_ticks(rng, 30_000, t0)
        t1 = t0 + 15 * 60 * SEC
        t_end = t1 + 60 * 60 * SEC
        rmask = ts < t1
        if rmask.sum() < 2:
            continue
        box = Box(high=float(px[rmask].max()), low=float(px[rmask].min()))
        if box.high == box.low:
            continue
        w = ts >= t1
        wts, wpx = ts[w], px[w]
        exact = label_path(wts, wpx, box, t_end)

        def ticks(t_open, bar_ms):
            m = (wts >= t_open) & (wts < t_open + bar_ms)
            return wts[m], wpx[m]

        for bar_ms, res in ((SEC, "1s"), (60 * SEC, "1m")):
            bars = bars_from_ticks(wts, wpx, bar_ms)
            drilled = label_bars(bars, box, t_end, lambda t, b=bar_ms: ticks(t, b))
            assert _same(exact, drilled), (bar_ms, exact, drilled)
            coarse = label_bars(bars, box, t_end)
            counts[f"{res}_ambig"] += coarse.outcome == AMBIG
            counts[f"{res}_wrong_without_ticks"] += coarse.outcome not in (AMBIG, exact.outcome)
        counts["cases"] += 1
    assert counts["cases"] > 200
    return counts


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                out = fn()
                print(f"PASS {name}" + (f"  {out}" if out else ""))
            except AssertionError as e:
                failures += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if failures else 0)
