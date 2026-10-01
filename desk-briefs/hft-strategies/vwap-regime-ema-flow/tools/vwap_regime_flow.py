"""VWAP regime + EMA 21/50/100 ribbon flow: research-only reference engine.

PAPER / RESEARCH ONLY. Nothing in this module talks to an exchange, holds keys,
or places orders. It exists to make the paper rule contract v0
(`../paper_rule_contract_v0.md`) executable on arbitrary OHLCV arrays so the
rules can be checked for causality and replayed on synthetic paths.

Synthetic paths are NOT historical data and results on them are NOT backtests.

Clock convention (same as the SD-MR track): every decision is taken at the
close of bar t and filled at the open of bar t+1. The session VWAP and its
residual sigma are frozen at t-1; EMAs and ATR include bar t because its close
is known at decision time.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from vwap_sd_mr_research import Bars, concat  # noqa: E402,F401

BAR_MIN = 5
SESSION_MIN = 1440
SESSION_BARS = SESSION_MIN // BAR_MIN

BULL_INTACT, BULL_WEAK, TANGLED, BEAR_WEAK, BEAR_INTACT = 2, 1, 0, -1, -2
RIBBON_NAMES = {2: "BULL_INTACT", 1: "BULL_WEAK", 0: "TANGLED", -1: "BEAR_WEAK", -2: "BEAR_INTACT"}


# --------------------------------------------------------------------------- #
# Session VWAP regime
# --------------------------------------------------------------------------- #


@dataclass
class RegimeParams:
    bar_minutes: int = BAR_MIN
    warmup_minutes: int = 60  # regime is UNDEFINED this long after the session anchor
    dead_band_sigma: float = 0.25  # a close must clear VWAP by this many residual sigmas to count as a side
    dead_band_floor_bps: float = 5.0
    accept_bars: int = 2  # consecutive closes beyond the dead band needed to crack the regime
    sigma_floor_bps: float = 3.0


@dataclass
class RegimeFrame:
    vwap_prev: np.ndarray
    sigma_prev: np.ndarray
    band: np.ndarray  # dead-band half-width in price units
    side_raw: np.ndarray  # +1 / -1 beyond the band, 0 inside it or undefined
    regime: np.ndarray  # +1 ABOVE, -1 BELOW, 0 UNDEFINED
    against: np.ndarray  # close beyond the band against the standing regime, not yet confirmed
    crack: np.ndarray  # +1 / -1 on the bar a regime is established or flipped, else 0
    regime_start: np.ndarray  # bar index where the standing regime began, -1 if undefined


def session_vwap_frozen(bars: Bars, sigma_floor_bps: float = 3.0) -> tuple[np.ndarray, np.ndarray]:
    """Typical-price session VWAP and volume-weighted residual sigma, through bar t-1.

    NaN on the first bar of every session: there is no prior bar in that session.
    """
    h, l, c, v, sess = bars.h, bars.l, bars.c, bars.v, bars.session
    n = len(c)
    tp = (h + l + c) / 3.0
    vwap_now = np.full(n, np.nan)
    sig_now = np.full(n, np.nan)
    sv = spv = sp2v = 0.0
    for t in range(n):
        if t == 0 or sess[t] != sess[t - 1]:
            sv = spv = sp2v = 0.0
        sv += v[t]
        spv += tp[t] * v[t]
        sp2v += tp[t] * tp[t] * v[t]
        if sv > 0:
            vw = spv / sv
            vwap_now[t] = vw
            sig_now[t] = np.sqrt(max(sp2v / sv - vw * vw, 0.0))
    vwap_prev = np.full(n, np.nan)
    sigma_prev = np.full(n, np.nan)
    same = np.zeros(n, bool)
    same[1:] = sess[1:] == sess[:-1]
    vwap_prev[1:] = np.where(same[1:], vwap_now[:-1], np.nan)
    sigma_prev[1:] = np.where(same[1:], sig_now[:-1], np.nan)
    sigma_prev = np.fmax(sigma_prev, sigma_floor_bps * 1e-4 * vwap_prev)
    return vwap_prev, sigma_prev


def vwap_regime(bars: Bars, p: RegimeParams = RegimeParams()) -> RegimeFrame:
    c, sess, minute = bars.c, bars.session, bars.minute
    n = len(c)
    vwap_prev, sigma_prev = session_vwap_frozen(bars, p.sigma_floor_bps)
    band = np.fmax(p.dead_band_sigma * sigma_prev, p.dead_band_floor_bps * 1e-4 * vwap_prev)
    ready = (minute >= p.warmup_minutes) & np.isfinite(vwap_prev)
    side_raw = np.zeros(n, int)
    side_raw[ready & (c > vwap_prev + band)] = 1
    side_raw[ready & (c < vwap_prev - band)] = -1

    regime = np.zeros(n, int)
    against = np.zeros(n, bool)
    crack = np.zeros(n, int)
    regime_start = np.full(n, -1)
    reg, streak, sside, start = 0, 0, 0, -1
    for t in range(n):
        if t == 0 or sess[t] != sess[t - 1]:
            reg, streak, sside, start = 0, 0, 0, -1
        if not ready[t]:
            continue
        s = side_raw[t]
        if s != 0 and s != reg:
            streak = streak + 1 if s == sside else 1
            sside = s
            if streak >= p.accept_bars:
                reg, streak, sside, start = s, 0, 0, t
                crack[t] = s
        else:
            streak, sside = 0, 0
        regime[t] = reg
        regime_start[t] = start
        against[t] = reg != 0 and s == -reg
    return RegimeFrame(vwap_prev, sigma_prev, band, side_raw, regime, against, crack, regime_start)


# --------------------------------------------------------------------------- #
# EMA 21 / 50 / 100 ribbon
# --------------------------------------------------------------------------- #


@dataclass
class RibbonParams:
    fast: int = 21
    mid: int = 50
    slow: int = 100
    atr_len: int = 14
    slope_bars: int = 6
    slope_min_atr: float = 0.05  # slow EMA must move at least this many ATRs over slope_bars
    sep_min_atr: float = 0.15  # both adjacent EMA gaps must be at least this wide to qualify
    sep_hold_atr: float = 0.05  # once intact, it stays intact until a gap shrinks below this
    confirm_bars: int = 6  # consecutive qualifying bars before the ribbon is called intact
    cross_lookback: int = 48
    max_fast_crosses: int = 2  # more EMA21/EMA50 crosses than this in the lookback means chop
    warmup_bars: int = 300  # 3 x slow; the EMA start value has decayed to < 0.3% weight by then


@dataclass
class RibbonFrame:
    e_fast: np.ndarray
    e_mid: np.ndarray
    e_slow: np.ndarray
    atr: np.ndarray
    order: np.ndarray  # +1 fast>mid>slow, -1 fast<mid<slow, 0 otherwise
    gap_atr: np.ndarray  # min adjacent gap in ATR units
    fast_crosses: np.ndarray
    qualify: np.ndarray  # +1 / -1 / 0: bar meets order + slope + separation + no-chop
    state: np.ndarray  # BULL_INTACT .. BEAR_INTACT
    ready: np.ndarray
    breaks: list[int] = field(default_factory=list)  # bars where INTACT dropped straight to TANGLED/opposite


def ema(x: np.ndarray, n: int) -> np.ndarray:
    """Seeded at the first value. The seed's weight after k bars is (1 - 2/(n+1))**k."""
    a = 2.0 / (n + 1.0)
    out = np.empty(len(x))
    out[0] = x[0]
    for t in range(1, len(x)):
        out[t] = out[t - 1] + a * (x[t] - out[t - 1])
    return out


def wilder_atr(h: np.ndarray, l: np.ndarray, c: np.ndarray, n: int) -> np.ndarray:
    tr = h - l
    tr[1:] = np.maximum.reduce([h[1:] - l[1:], np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])])
    out = np.empty(len(tr))
    out[0] = tr[0]
    for t in range(1, len(tr)):
        out[t] = out[t - 1] + (tr[t] - out[t - 1]) / n
    return out


def ribbon(bars: Bars, p: RibbonParams = RibbonParams()) -> RibbonFrame:
    c = bars.c
    n = len(c)
    ef, em, es = ema(c, p.fast), ema(c, p.mid), ema(c, p.slow)
    atr = wilder_atr(bars.h.copy(), bars.l, c, p.atr_len)
    order = np.where((ef > em) & (em > es), 1, np.where((ef < em) & (em < es), -1, 0))
    gap_atr = np.minimum(np.abs(ef - em), np.abs(em - es)) / atr

    k = p.slope_bars
    d_f, d_m, d_s = np.zeros(n), np.zeros(n), np.zeros(n)
    d_f[k:], d_m[k:], d_s[k:] = ef[k:] - ef[:-k], em[k:] - em[:-k], es[k:] - es[:-k]
    slope_bull = (d_f > 0) & (d_m > 0) & (d_s >= p.slope_min_atr * atr)
    slope_bear = (d_f < 0) & (d_m < 0) & (-d_s >= p.slope_min_atr * atr)

    fm_sign = np.sign(ef - em)
    flips = np.zeros(n, int)
    flips[1:] = (fm_sign[1:] != fm_sign[:-1]) & (fm_sign[1:] != 0)
    fast_crosses = np.array([flips[max(0, t - p.cross_lookback + 1) : t + 1].sum() for t in range(n)])

    sep_ok = gap_atr >= p.sep_min_atr
    calm = fast_crosses <= p.max_fast_crosses
    qualify = np.where((order == 1) & slope_bull & sep_ok & calm, 1, np.where((order == -1) & slope_bear & sep_ok & calm, -1, 0))

    ready = np.arange(n) >= p.warmup_bars
    state = np.zeros(n, int)
    breaks: list[int] = []
    st, streak, sdir = 0, 0, 0
    for t in range(n):
        q = qualify[t]
        if q != 0 and q == sdir:
            streak += 1
        elif q != 0:
            streak, sdir = 1, q
        else:
            streak, sdir = 0, 0
        if not ready[t]:
            continue
        o = order[t]
        if abs(st) == 2:
            d = st // 2
            mid_slope_ok = np.sign(d_m[t]) == d
            if o == d and gap_atr[t] >= p.sep_hold_atr and mid_slope_ok:
                pass
            elif o == d:
                st = d
            else:
                st = 0 if o == 0 else o
                breaks.append(t)
        elif streak >= p.confirm_bars:
            st = 2 * sdir
        elif o != 0 and calm[t]:
            st = o
        else:
            st = 0
        state[t] = st
    return RibbonFrame(ef, em, es, atr, order, gap_atr, fast_crosses, qualify, state, ready, breaks)


def cell(regime: int, ribbon_state: int) -> str:
    """Decision-matrix cell for one bar: AGREE, WEAK, TANGLED, CONFLICT or UNDEFINED."""
    if regime == 0:
        return "UNDEFINED"
    a = regime * ribbon_state
    if a == 2:
        return "AGREE"
    if a == 1:
        return "WEAK"
    if a < 0:
        return "CONFLICT"
    return "TANGLED"


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #


def minutes_left(bars: Bars, t: int, bar_minutes: int = BAR_MIN) -> int:
    """Minutes left in the session once bar t has closed."""
    return SESSION_MIN - (int(bars.minute[t]) + bar_minutes)


def blackout_mask(n: int, ranges: tuple[tuple[int, int], ...]) -> np.ndarray:
    m = np.zeros(n, bool)
    for a, b in ranges:
        m[a:b] = True
    return m


# --------------------------------------------------------------------------- #
# Book B: perp directional overlay
# --------------------------------------------------------------------------- #


@dataclass
class PerpParams:
    bar_minutes: int = BAR_MIN
    no_entry_last_minutes: int = 60
    flat_before_end_minutes: int = 15
    cooldown_bars: int = 6
    max_entries_per_regime: int = 2
    stop_atr_min: float = 2.0  # hard stop at least this many ATRs from entry ...
    stop_vwap_buffer_atr: float = 0.5  # ... and beyond the far edge of the VWAP dead band by this much; R = entry-to-stop
    add_at_r: float = 1.0
    add_units: float = 0.5
    reduce_frac: float = 0.5
    time_stop_bars: int = 48
    time_stop_min_r: float = 0.5  # time stop fires if MFE has not reached this many R by time_stop_bars
    max_hold_bars: int = 144
    taker_bps: float = 5.0  # paper placeholder; replace with the venue tier
    slippage_bps: float = 1.0
    funding_minutes: tuple[int, ...] = (0, 480, 960)  # per symbol in reality; read the venue's funding schedule
    funding_bps: float = 1.0  # per stamp, longs pay when positive; placeholder for the printed rate
    funding_blackout_minutes: int = 10
    blackout: tuple[tuple[int, int], ...] = ()  # absolute bar ranges (event placeholders)
    daily_loss_r: float = 3.0
    max_consec_losses: int = 3
    use_ribbon_gate: bool = True


@dataclass
class Fill:
    t: int
    units: float  # signed change
    px: float
    reason: str


@dataclass
class Episode:
    side: int
    signal_t: int
    entry_t: int
    entry_px: float
    r_px: float  # 1R in price units
    stop_px: float
    exit_t: int | None = None
    exit_reason: str = "OPEN"
    pnl_bps: float = 0.0  # net, per 1 unit of initial size, at entry price
    cost_bps: float = 0.0
    funding_bps: float = 0.0
    mfe_r: float = 0.0
    mae_r: float = 0.0
    max_units: float = 1.0
    added: bool = False
    reduced: bool = False

    @property
    def r_bps(self) -> float:
        return self.r_px / self.entry_px * 1e4

    @property
    def r_multiple(self) -> float:
        return self.pnl_bps / self.r_bps


@dataclass
class PerpResult:
    position: np.ndarray  # units held at the close of bar t
    equity_bps: np.ndarray  # cumulative net P&L, bps of one unit at the first close
    episodes: list[Episode]
    fills: list[Fill]
    events: list[tuple[int, str]]


def _funding_soon(fill_minute: int, p: PerpParams) -> bool:
    return any(0 <= (fm - fill_minute) % SESSION_MIN < p.funding_blackout_minutes for fm in p.funding_minutes)


def run_perp(bars: Bars, rf: RegimeFrame, rb: RibbonFrame, p: PerpParams = PerpParams()) -> PerpResult:
    o, h, l, c, sess, minute = bars.o, bars.h, bars.l, bars.c, bars.session, bars.minute
    n = len(c)
    ref = c[0]
    blk = blackout_mask(n, p.blackout)
    position = np.zeros(n)
    equity = np.zeros(n)
    episodes: list[Episode] = []
    fills: list[Fill] = []
    events: list[tuple[int, str]] = []

    pos = 0.0
    ep: Episode | None = None
    pending: tuple[float, str, int, float] | None = None  # target units, reason, signal bar, structural stop
    cool_until = -1
    entries_in_regime: dict[int, int] = {}
    sess_r = 0.0
    consec = 0
    sess_off = False
    eq = 0.0

    def trade(t: int, target: float, px: float, reason: str) -> float:
        nonlocal pos
        d = target - pos
        cost = abs(d) * px * (p.taker_bps + p.slippage_bps) * 1e-4
        fills.append(Fill(t, d, px, reason))
        events.append((t, reason))
        pos = target
        if ep is not None:
            ep.cost_bps += cost / ep.entry_px * 1e4
            ep.pnl_bps -= cost / ep.entry_px * 1e4
            ep.max_units = max(ep.max_units, abs(pos))
        return cost

    def close_episode(t: int, reason: str) -> None:
        nonlocal ep, cool_until, sess_r, consec, sess_off
        assert ep is not None
        ep.exit_t, ep.exit_reason = t, reason
        episodes.append(ep)
        r = ep.r_multiple
        sess_r += r
        consec = consec + 1 if ep.pnl_bps < 0 else 0
        if sess_r <= -p.daily_loss_r or consec >= p.max_consec_losses:
            if not sess_off:
                events.append((t, "KILL_SESSION_LOSS_LIMIT"))
            sess_off = True
        ep, cool_until = None, t + p.cooldown_bars

    for t in range(n):
        if t > 0 and sess[t] != sess[t - 1]:
            sess_r, consec, sess_off = 0.0, 0, False
        prev_px = c[t - 1] if t > 0 else o[t]
        pnl = pos * (o[t] - prev_px)
        if pos != 0 and int(minute[t]) % SESSION_MIN in p.funding_minutes:
            f = pos * p.funding_bps * 1e-4 * o[t]
            pnl -= f
            if ep is not None:
                ep.funding_bps += f / ep.entry_px * 1e4
                ep.pnl_bps -= f / ep.entry_px * 1e4
        if ep is not None:
            ep.pnl_bps += pos * (o[t] - prev_px) / ep.entry_px * 1e4

        if pending is not None:
            target, reason, sig_t, sig_stop = pending
            pending = None
            if pos == 0 and target != 0:
                side = int(np.sign(target))
                min_px = o[t] - side * p.stop_atr_min * rb.atr[sig_t]
                stop_px = min(min_px, sig_stop) if side > 0 else max(min_px, sig_stop)
                ep = Episode(side, sig_t, t, o[t], abs(o[t] - stop_px), stop_px)
                pnl -= trade(t, target, o[t], reason)
            elif target == 0 and ep is not None:
                pnl -= trade(t, 0.0, o[t], reason)
                close_episode(t, reason)
            elif ep is not None:
                pnl -= trade(t, target, o[t], reason)
                if reason == "ADD":
                    ep.added, ep.stop_px = True, ep.entry_px
                else:
                    ep.reduced = True

        if ep is not None:
            s = ep.side
            hit = (l[t] <= ep.stop_px) if s > 0 else (h[t] >= ep.stop_px)
            if hit:
                gap = (o[t] < ep.stop_px) if s > 0 else (o[t] > ep.stop_px)
                px = o[t] if gap else ep.stop_px
                move = pos * (px - o[t])
                pnl += move
                ep.pnl_bps += move / ep.entry_px * 1e4
                ep.mae_r = min(ep.mae_r, s * (px - ep.entry_px) / ep.r_px)
                pnl -= trade(t, 0.0, px, "STOP")
                close_episode(t, "STOP")
            else:
                move = pos * (c[t] - o[t])
                pnl += move
                ep.pnl_bps += move / ep.entry_px * 1e4
                ep.mfe_r = max(ep.mfe_r, s * ((h[t] if s > 0 else l[t]) - ep.entry_px) / ep.r_px)
                ep.mae_r = min(ep.mae_r, s * ((l[t] if s > 0 else h[t]) - ep.entry_px) / ep.r_px)

        eq += pnl / ref * 1e4
        equity[t] = eq
        position[t] = pos
        if t + 1 >= n:
            continue

        left = minutes_left(bars, t, p.bar_minutes)
        new_sess_next = sess[t + 1] != sess[t]
        reg, rbs, sraw = rf.regime[t], rb.state[t], rf.side_raw[t]

        if ep is not None:
            s = ep.side
            held = t - ep.entry_t + 1
            reason = None
            if new_sess_next or left <= p.flat_before_end_minutes:
                reason = "SESSION_FLAT"
            elif blk[t + 1]:
                reason = "EVENT_FLAT"
            elif reg == -s:
                reason = "KILL_VWAP_RECROSS"
            elif p.use_ribbon_gate and rbs * s <= 0:
                reason = "KILL_RIBBON_BREAK"
            elif held >= p.max_hold_bars:
                reason = "MAX_HOLD"
            elif held >= p.time_stop_bars and ep.mfe_r < p.time_stop_min_r:
                reason = "TIME_STOP"
            if reason:
                pending = (0.0, reason, t, np.nan)
                continue
            open_r = s * (c[t] - ep.entry_px) / ep.r_px
            if not ep.reduced and p.use_ribbon_gate and rbs * s == 1:
                pending = (pos * p.reduce_frac, "REDUCE_RIBBON_WEAK", t, np.nan)
            elif not ep.reduced and sraw != s:
                pending = (pos * p.reduce_frac, "REDUCE_VWAP_TOUCH", t, np.nan)
            elif (
                not ep.added
                and not ep.reduced
                and open_r >= p.add_at_r
                and (not p.use_ribbon_gate or rbs * s == 2)
                and sraw == s
                and left > p.no_entry_last_minutes
            ):
                pending = (pos + s * p.add_units, "ADD", t, np.nan)
            continue

        if reg == 0 or sess_off or t < cool_until:
            continue
        if sraw != reg or left <= p.no_entry_last_minutes or new_sess_next:
            continue
        start = int(rf.regime_start[t])
        if entries_in_regime.get(start, 0) >= p.max_entries_per_regime:
            continue
        fill_minute = int(minute[t]) + p.bar_minutes
        if blk[t + 1] or _funding_soon(fill_minute, p):
            events.append((t, "BLOCKED_WINDOW"))
            continue
        if p.use_ribbon_gate and not (rb.ready[t] and rbs == 2 * reg):
            events.append((t, "BLOCKED_CONFLICT" if rbs * reg < 0 else "BLOCKED_TANGLED"))
            continue
        entries_in_regime[start] = entries_in_regime.get(start, 0) + 1
        struct_stop = rf.vwap_prev[t] - reg * (rf.band[t] + p.stop_vwap_buffer_atr * rb.atr[t])
        pending = (float(reg), "ENTRY_LONG" if reg > 0 else "ENTRY_SHORT", t, struct_stop)
        events.append((t, "SIGNAL_LONG" if reg > 0 else "SIGNAL_SHORT"))

    if ep is not None:
        episodes.append(ep)
    return PerpResult(position, equity, episodes, fills, events)


def run_side_follow(
    bars: Bars, rf: RegimeFrame, rb: RibbonFrame | None = None, cost_bps: float = 6.0, bar_minutes: int = BAR_MIN
) -> tuple[np.ndarray, np.ndarray, int]:
    """Comparator: hold +1/-1 = regime (optionally only when the ribbon agrees), flat at session end.

    Returns (position, equity_bps, number of position changes). Used to show whipsaw and
    gate trade-offs, not as a candidate strategy.
    """
    o, c, sess = bars.o, bars.c, bars.session
    n = len(c)
    want = rf.regime.astype(float).copy()
    if rb is not None:
        want = np.where(rb.ready & (rb.state == 2 * rf.regime), want, 0.0)
    for t in range(n):
        if minutes_left(bars, t, bar_minutes) <= 15 or (t + 1 < n and sess[t + 1] != sess[t]):
            want[t] = 0.0
    pos = np.zeros(n)
    eq = np.zeros(n)
    cur, e, changes = 0.0, 0.0, 0
    for t in range(n):
        prev = c[t - 1] if t > 0 else o[t]
        pnl = cur * (o[t] - prev)
        if t > 0 and want[t - 1] != cur:
            pnl -= abs(want[t - 1] - cur) * o[t] * cost_bps * 1e-4
            cur = want[t - 1]
            changes += 1
        pnl += cur * (c[t] - o[t])
        e += pnl / c[0] * 1e4
        pos[t], eq[t] = cur, e
    return pos, eq, changes


# --------------------------------------------------------------------------- #
# Book A: inventory-skew paper book
# --------------------------------------------------------------------------- #


@dataclass
class InventoryParams:
    bar_minutes: int = BAR_MIN
    q_max: float = 1.0
    lean: float = 0.6  # target |inventory| in AGREE, as a fraction of q_max
    mult_agree: float = 1.0
    mult_weak: float = 0.5
    mult_tangled: float = 0.0
    mult_conflict: float = 0.0
    clip: float = 0.1  # quote size per side per bar
    half_spread_bps_min: float = 2.0
    half_spread_vol: float = 0.5  # half-spread as a multiple of the trailing 5m return sd
    vol_len: int = 48
    skew_k: float = 1.5  # quote shift in half-spreads per unit of (q* - q) / q_max
    skew_cap: float = 0.9  # keeps both quotes passive
    tick_bps: float = 0.5  # a passive quote fills only if the bar trades through it by this much
    maker_bps: float = 1.0  # paper placeholders
    taker_bps: float = 6.0
    no_absorb_against_lean: bool = True
    drift_tol: float = 0.5  # |q - q*| above this (x q_max) ...
    drift_bars: int = 24  # ... for this many bars triggers a taker unwind
    unwind_clip: float = 0.1
    flat_window_minutes: int = 30  # target goes to 0 this close to session end
    hard_flat_minutes: int = 10  # residual inventory crossed out this close to session end
    blackout: tuple[tuple[int, int], ...] = ()


@dataclass
class InvFill:
    t: int
    qty: float  # signed: + bought, - sold
    px: float
    maker: bool
    regime: int
    q_target: float  # target at the decision that placed the quote


@dataclass
class InventoryResult:
    q_target: np.ndarray  # target set at the close of bar t (applies to quotes for bar t+1)
    q: np.ndarray  # inventory at the close of bar t
    equity_bps: np.ndarray  # bps of q_max notional at the first close
    fills: list[InvFill]
    events: list[tuple[int, str]]


def inventory_target(t: int, bars: Bars, rf: RegimeFrame, rb: RibbonFrame, p: InventoryParams, blk: np.ndarray) -> float:
    reg = int(rf.regime[t])
    if reg == 0 or rf.against[t] or blk[min(t + 1, len(blk) - 1)]:
        return 0.0
    if minutes_left(bars, t, p.bar_minutes) <= p.flat_window_minutes:
        return 0.0
    k = cell(reg, int(rb.state[t]) if rb.ready[t] else 0)
    m = {"AGREE": p.mult_agree, "WEAK": p.mult_weak, "TANGLED": p.mult_tangled}.get(k, p.mult_conflict)
    return reg * p.lean * p.q_max * m


def run_inventory(bars: Bars, rf: RegimeFrame, rb: RibbonFrame, p: InventoryParams = InventoryParams()) -> InventoryResult:
    o, h, l, c = bars.o, bars.h, bars.l, bars.c
    n = len(c)
    ref = c[0]
    blk = blackout_mask(n, p.blackout)
    r = np.zeros(n)
    r[1:] = np.log(c[1:] / c[:-1])
    q_target = np.zeros(n)
    q_arr = np.zeros(n)
    equity = np.zeros(n)
    fills: list[InvFill] = []
    events: list[tuple[int, str]] = []

    q, cash, fees = 0.0, 0.0, 0.0
    quotes: tuple[float, float, float, float, int, float] | None = None  # bid, bid_sz, ask, ask_sz, regime, q*
    taker: tuple[float, str] | None = None
    drift_run = 0

    for t in range(n):
        if taker is not None:
            qty, why = taker
            cash -= qty * o[t]
            fees += abs(qty) * o[t] * p.taker_bps * 1e-4
            q += qty
            fills.append(InvFill(t, qty, o[t], False, int(rf.regime[t - 1]), q_target[t - 1]))
            events.append((t, why))
            taker = None
        if quotes is not None:
            bid, bsz, ask, asz, reg_q, tgt = quotes
            if bsz > 0 and l[t] <= bid * (1 - p.tick_bps * 1e-4):
                cash -= bsz * bid
                fees += bsz * bid * p.maker_bps * 1e-4
                q += bsz
                fills.append(InvFill(t, bsz, bid, True, reg_q, tgt))
            if asz > 0 and h[t] >= ask * (1 + p.tick_bps * 1e-4):
                cash += asz * ask
                fees += asz * ask * p.maker_bps * 1e-4
                q -= asz
                fills.append(InvFill(t, -asz, ask, True, reg_q, tgt))
            quotes = None

        q_arr[t] = q
        equity[t] = (cash + q * c[t] - fees) / (p.q_max * ref) * 1e4
        if t + 1 >= n:
            continue

        tgt = inventory_target(t, bars, rf, rb, p, blk)
        q_target[t] = tgt
        left = minutes_left(bars, t, p.bar_minutes)
        if left <= p.hard_flat_minutes or bars.session[t + 1] != bars.session[t]:
            if abs(q) > 1e-12:
                taker = (-q, "SESSION_FLAT")
            continue
        if blk[t + 1]:
            if abs(q) > 1e-12:
                taker = (-q, "EVENT_FLAT")
            continue

        drift_run = drift_run + 1 if abs(q - tgt) > p.drift_tol * p.q_max else 0
        if drift_run >= p.drift_bars:
            step = float(np.clip(tgt - q, -p.unwind_clip, p.unwind_clip))
            taker = (step, "INVENTORY_UNWIND")
            drift_run = 0

        lo = max(1, t - p.vol_len + 1)
        sd_bps = float(np.std(r[lo : t + 1]) * 1e4) if t >= 2 else p.half_spread_bps_min
        hs = max(p.half_spread_bps_min, p.half_spread_vol * sd_bps) * 1e-4 * c[t]
        skew = float(np.clip(p.skew_k * (tgt - q) / p.q_max, -p.skew_cap, p.skew_cap))
        bid = c[t] - hs + skew * hs
        ask = c[t] + hs + skew * hs
        bsz = p.clip if q + p.clip <= p.q_max + 1e-12 else 0.0
        asz = p.clip if q - p.clip >= -p.q_max - 1e-12 else 0.0
        if p.no_absorb_against_lean:
            if tgt < 0 and q >= tgt:
                bsz = 0.0
            if tgt > 0 and q <= tgt:
                asz = 0.0
        quotes = (bid, bsz, ask, asz, int(rf.regime[t]), tgt)

    return InventoryResult(q_target, q_arr, equity, fills, events)


def markouts(bars: Bars, fills: list[InvFill], horizons: tuple[int, ...] = (1, 3, 6, 12)) -> dict[str, np.ndarray]:
    """Per maker fill: signed markout in bps at each horizon (bars), plus tags.

    Positive markout = the fill was on the right side of the subsequent move.
    """
    c = bars.c
    rows = []
    for f in fills:
        if not f.maker:
            continue
        side = 1 if f.qty > 0 else -1
        mk = [side * (c[f.t + k] - f.px) / f.px * 1e4 if f.t + k < len(c) else np.nan for k in horizons]
        with_lean = (f.q_target != 0) and (np.sign(f.q_target) == side)
        rows.append((*mk, side, f.regime, with_lean))
    if not rows:
        return {"markout": np.zeros((0, len(horizons))), "side": np.zeros(0), "regime": np.zeros(0), "with_lean": np.zeros(0, bool)}
    a = np.array(rows, dtype=float)
    k = len(horizons)
    return {"markout": a[:, :k], "side": a[:, k], "regime": a[:, k + 1], "with_lean": a[:, k + 2].astype(bool)}


# --------------------------------------------------------------------------- #
# Synthetic 5m paths (educational only)
# --------------------------------------------------------------------------- #

SUB = 20  # fine steps per 5m bar for realistic highs and lows


@dataclass
class Seg:
    bars: int
    drift_bps: float  # per-bar drift of the anchor
    vol_bps: float  # per-bar diffusion
    theta: float = 0.0  # per-bar pull of price toward the drifting anchor (0 = random walk)


def synth_path(seed: int, segs: list[Seg], p0: float = 100.0, session0: int = 0) -> Bars:
    rng = np.random.default_rng(seed)
    total = sum(s.bars for s in segs)
    fine = np.empty(total * SUB + 1)
    fine[0] = np.log(p0)
    anchor = fine[0]
    vol_bar = np.empty(total)
    i = 1
    b0 = 0
    for s in segs:
        dt = 1.0 / SUB
        for _ in range(s.bars * SUB):
            anchor += s.drift_bps * 1e-4 * dt
            pull = s.theta * (anchor - fine[i - 1]) * dt
            fine[i] = fine[i - 1] + pull + s.vol_bps * 1e-4 * np.sqrt(dt) * rng.standard_normal()
            i += 1
        vol_bar[b0 : b0 + s.bars] = s.vol_bps
        b0 += s.bars
    px = np.exp(fine)
    o = px[0:-1:SUB][:total]
    c = px[SUB::SUB][:total]
    h = np.array([px[k * SUB : (k + 1) * SUB + 1].max() for k in range(total)])
    lo = np.array([px[k * SUB : (k + 1) * SUB + 1].min() for k in range(total)])
    idx = np.arange(total)
    minute = (idx % SESSION_BARS) * BAR_MIN
    hour = minute / 60.0
    intraday = 1.0 + 0.6 * np.exp(-0.5 * ((hour - 14.5) / 2.0) ** 2)
    rng_rel = (h - lo) / np.median(h - lo)
    v = 100.0 * intraday * (0.5 + 0.5 * rng_rel) * rng.lognormal(0.0, 0.3, total)
    return Bars(o, h, lo, c, v, idx // SESSION_BARS + session0, minute)


def last_session(bars: Bars) -> slice:
    s = bars.session[-1]
    idx = np.flatnonzero(bars.session == s)
    return slice(int(idx[0]), int(idx[-1]) + 1)
