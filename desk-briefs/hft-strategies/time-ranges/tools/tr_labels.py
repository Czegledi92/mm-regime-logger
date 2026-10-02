"""Reference labeler for BTC perp time-based ranges (TR label algebra v0). PAPER / RESEARCH ONLY.

Implements section 4 of 20261003-btc-perp-time-range-investigation.md. Where the brief and this file
disagree, one of them is wrong: fix it, do not interpret.

Two entry points:

* ``label_path``: exact labels from prints in execution order (trade or aggTrade id order).
* ``label_bars``: labels from 1 s or 1 m OHLC bars. Each bar's high and low are tried in both orders.
  Bars that host a decisive point (break, reversal, deepest pullback, extreme) are replaced by their
  trades through ``ticks_for_bar`` until every decisive point sits in tick data. Without tick data, a
  label that depends on the intra-bar order comes back ``AMBIG``.

No signal, no sizing, no order path.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Callable, Optional

import numpy as np

NO_BREAK = "NO_BREAK"
CONTINUATION = "CONTINUATION"
REVERSAL = "REVERSAL"
UNRESOLVED = "UNRESOLVED"
AMBIG = "AMBIG"

MARKOUT_MS = 180_000


@dataclass(frozen=True)
class Box:
    high: float
    low: float

    @property
    def mid(self) -> float:
        return 0.5 * (self.high + self.low)

    @property
    def size_bps(self) -> float:
        return 1e4 * (self.high - self.low) / self.mid


@dataclass
class Label:
    outcome: str
    side: int = 0
    size_bps: float = np.nan
    t_break: Optional[int] = None
    t_reversal: Optional[int] = None
    ife_bps: float = np.nan
    heat_bps: float = np.nan
    pullback_bps: float = np.nan
    mfe_bps: float = np.nan
    t_ife: Optional[int] = None
    t_heat: Optional[int] = None
    t_mfe: Optional[int] = None
    ext_bps: float = np.nan
    t_ext: Optional[int] = None
    rev_ife_bps: float = np.nan
    rev_heat_bps: float = np.nan
    rev_pullback_bps: float = np.nan
    rev_mfe_bps: float = np.nan
    t_rev_heat: Optional[int] = None
    t_rev_mfe: Optional[int] = None
    ret_180s_bps: float = np.nan
    ret_end_bps: float = np.nan
    resolution: str = "tick"
    exact: bool = True
    idx: dict = field(default_factory=dict, repr=False)


def _decompose(x: np.ndarray) -> tuple[int, int, int]:
    """Indices of IFE, deepest pullback (heat) and MFE for one leg.

    ``x`` is the leg in signed bps from its reference edge, positive in the leg's direction, starting
    at the leg's first print. Heat is the last print at the leg's minimum, so a continuation needs a new
    extreme after the final visit of the deepest low. IFE is the highest print up to the heat. MFE is
    the first print at the leg's maximum.
    """
    lo = x.min()
    i_heat = int(np.flatnonzero(x == lo)[-1])
    i_ife = int(np.argmax(x[: i_heat + 1]))
    i_mfe = int(np.argmax(x))
    return i_ife, i_heat, i_mfe


def label_path(ts: np.ndarray, px: np.ndarray, box: Box, t_end: int) -> Label:
    """Label one observation window from prints in execution order.

    ``ts`` (epoch ms, non-decreasing) and ``px`` start at the window open. Labels use prints with
    ``ts < t_end``. Prints at or after ``t_end`` are read only for the 180 s markout.
    """
    ts = np.asarray(ts, dtype=np.int64)
    px = np.asarray(px, dtype=float)
    n = int(np.searchsorted(ts, t_end, side="left"))
    mid, size = box.mid, box.size_bps
    lab = Label(outcome=NO_BREAK, size_bps=size)
    if n == 0:
        return lab

    hit = np.flatnonzero((px[:n] > box.high) | (px[:n] < box.low))
    if hit.size == 0:
        return lab
    ib = int(hit[0])
    side = 1 if px[ib] > box.high else -1
    edge = box.high if side == 1 else box.low
    opp = box.low if side == 1 else box.high
    x = side * (px - edge) / mid * 1e4
    lab.side, lab.t_break = side, int(ts[ib])
    lab.idx["break"] = ib

    beyond_opp = np.flatnonzero(side * (px[ib + 1 : n] - opp) < 0)
    ir = ib + 1 + int(beyond_opp[0]) if beyond_opp.size else None

    k = int(np.searchsorted(ts, ts[ib] + MARKOUT_MS, side="right")) - 1
    lab.ret_180s_bps = float(side * (px[k] - px[ib]) / mid * 1e4)
    lab.ret_end_bps = float(side * (px[n - 1] - px[ib]) / mid * 1e4)
    lab.idx.update(m180=k, end=n - 1)

    if ir is None:
        leg = x[ib:n]
        i_ife, i_heat, i_mfe = (ib + j for j in _decompose(leg))
        lab.ife_bps, lab.mfe_bps = float(x[i_ife]), float(x[i_mfe])
        lab.heat_bps = float(-x[i_heat])
        lab.pullback_bps = float(x[i_ife] - x[i_heat])
        lab.t_ife, lab.t_heat, lab.t_mfe = int(ts[i_ife]), int(ts[i_heat]), int(ts[i_mfe])
        lab.idx.update(ife=i_ife, heat=i_heat, mfe=i_mfe)
        lab.outcome = CONTINUATION if x[i_mfe] > x[i_ife] else UNRESOLVED
        return lab

    lab.outcome = REVERSAL
    lab.t_reversal = int(ts[ir])
    lab.idx["reversal"] = ir
    i_ext = ib + int(np.argmax(x[ib:ir]))
    lab.ext_bps, lab.t_ext = float(x[i_ext]), int(ts[i_ext])
    lab.idx["ext"] = i_ext

    y = -side * (px - opp) / mid * 1e4
    leg = y[ir:n]
    j_ife, j_heat, j_mfe = (ir + j for j in _decompose(leg))
    lab.rev_ife_bps, lab.rev_mfe_bps = float(y[j_ife]), float(y[j_mfe])
    lab.rev_heat_bps = float(-y[j_heat])
    lab.rev_pullback_bps = float(y[j_ife] - y[j_heat])
    lab.t_rev_heat, lab.t_rev_mfe = int(ts[j_heat]), int(ts[j_mfe])
    lab.idx.update(rev_ife=j_ife, rev_heat=j_heat, rev_mfe=j_mfe)
    return lab


@dataclass
class Bars:
    """OHLC bars keyed by open time (epoch ms). Bars with ``count == 0`` carry no prints and are skipped."""

    t_open: np.ndarray
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    count: np.ndarray
    bar_ms: int

    def traded(self) -> "Bars":
        m = np.asarray(self.count) > 0
        return Bars(*(np.asarray(a)[m] for a in (self.t_open, self.o, self.h, self.l, self.c, self.count)), self.bar_ms)


def bars_from_ticks(ts: np.ndarray, px: np.ndarray, bar_ms: int) -> Bars:
    ts = np.asarray(ts, dtype=np.int64)
    px = np.asarray(px, dtype=float)
    key = ts // bar_ms * bar_ms
    starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    ends = np.r_[starts[1:], len(ts)]
    return Bars(
        t_open=key[starts],
        o=px[starts],
        h=np.maximum.reduceat(px, starts),
        l=np.minimum.reduceat(px, starts),
        c=px[ends - 1],
        count=ends - starts,
        bar_ms=bar_ms,
    )


def box_from_bars(bars: Bars, t0: int, t1: int) -> Box:
    b = bars.traded()
    m = (b.t_open >= t0) & (b.t_open < t1)
    return Box(high=float(b.h[m].max()), low=float(b.l[m].min()))


def _build(bars: Bars, expanded: dict, high_first: bool):
    """Pseudo-prints O, H, L, C (or O, L, H, C) per bar, with expanded bars spliced in as ticks."""
    n = len(bars.t_open)
    mid = (bars.h, bars.l) if high_first else (bars.l, bars.h)
    base_px = np.stack([bars.o, *mid, bars.c], axis=1).astype(float).ravel()
    base_ts = np.repeat(np.asarray(bars.t_open, dtype=np.int64), 4)
    base_owner = np.repeat(np.arange(n), 4)
    if not expanded:
        return base_ts, base_px, base_owner
    ts, px, owner, prev = [], [], [], 0
    for j in sorted(expanded):
        ts.append(base_ts[4 * prev : 4 * j])
        px.append(base_px[4 * prev : 4 * j])
        owner.append(base_owner[4 * prev : 4 * j])
        tts, tpx = expanded[j]
        ts.append(np.asarray(tts, dtype=np.int64))
        px.append(np.asarray(tpx, dtype=float))
        owner.append(np.full(len(tts), j))
        prev = j + 1
    ts.append(base_ts[4 * prev :])
    px.append(base_px[4 * prev :])
    owner.append(base_owner[4 * prev :])
    return np.concatenate(ts), np.concatenate(px), np.concatenate(owner)


def _key(lab: Label) -> tuple:
    vals = (lab.ife_bps, lab.heat_bps, lab.mfe_bps, lab.ext_bps, lab.rev_ife_bps, lab.rev_heat_bps, lab.rev_mfe_bps)
    return (lab.outcome, lab.side, lab.t_break, lab.t_reversal, *(None if np.isnan(v) else round(v, 9) for v in vals))


def label_bars(
    bars: Bars,
    box: Box,
    t_end: int,
    ticks_for_bar: Optional[Callable[[int], tuple[np.ndarray, np.ndarray]]] = None,
    max_rounds: int = 8,
) -> Label:
    """Label from bars, drilling into ticks for every bar that hosts a decisive point.

    ``ticks_for_bar(t_open)`` returns ``(ts, px)`` for that bar in execution order. ``bars`` must
    cover the window open through ``t_end`` (and 180 s beyond if the markout is wanted).
    """
    if t_end % bars.bar_ms:
        raise ValueError("t_end must fall on a bar boundary, or the last bar leaks prints from after the window")
    b = bars.traded()
    expanded: dict = {}
    for _ in range(max_rounds):
        runs = []
        for high_first in (True, False):
            ts, px, owner = _build(b, expanded, high_first)
            lab = label_path(ts, px, box, t_end)
            crit = {int(owner[i]) for i in lab.idx.values()}
            runs.append((lab, crit))
        (la, ca), (lb, cb) = runs
        todo = (ca | cb) - set(expanded)
        if not todo:
            if _key(la) != _key(lb):
                raise AssertionError("orderings disagree with every decisive bar in ticks")
            la.resolution = "tick" if expanded else f"{b.bar_ms}ms"
            return la
        if ticks_for_bar is None:
            if la.outcome != lb.outcome or la.side != lb.side:
                return Label(outcome=AMBIG, size_bps=box.size_bps, resolution=f"{b.bar_ms}ms", exact=False)
            out = replace(la, resolution=f"{b.bar_ms}ms", exact=False)
            return out
        for j in todo:
            expanded[j] = ticks_for_bar(int(b.t_open[j]))
    raise RuntimeError("drill-down did not converge")
