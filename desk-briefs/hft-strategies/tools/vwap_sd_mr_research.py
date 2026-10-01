"""VWAP standard-deviation mean-reversion: research-only reference implementations.

PAPER / RESEARCH ONLY. Nothing in this module talks to an exchange, holds keys,
or places orders. It exists to (a) reproduce the vault Pine logic bar-for-bar on
arbitrary OHLCV arrays, (b) run the proposed paper v1 contract on the same bars,
and (c) generate seeded synthetic 1-minute paths for educational figures.

Synthetic paths are NOT historical data and results on them are NOT backtests.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


# --------------------------------------------------------------------------- #
# Bars
# --------------------------------------------------------------------------- #


@dataclass
class Bars:
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    v: np.ndarray
    session: np.ndarray  # integer session id per bar
    minute: np.ndarray  # minutes since that bar's session anchor

    def __len__(self) -> int:
        return len(self.c)

    def slice(self, start: int, stop: int | None = None) -> "Bars":
        s = slice(start, stop)
        return Bars(self.o[s], self.h[s], self.l[s], self.c[s], self.v[s], self.session[s], self.minute[s])


@dataclass
class Trade:
    side: int  # +1 long, -1 short
    signal_t: int
    entry_t: int
    entry_px: float
    exit_t: int | None = None
    exit_px: float | None = None
    reason: str = "OPEN"
    entry_cost_bps: float = 0.0
    exit_cost_bps: float = 0.0

    @property
    def gross_bps(self) -> float:
        if self.exit_px is None:
            return float("nan")
        return self.side * (self.exit_px / self.entry_px - 1.0) * 1e4

    @property
    def net_bps(self) -> float:
        return self.gross_bps - self.entry_cost_bps - self.exit_cost_bps


# --------------------------------------------------------------------------- #
# Vault logic, reproduced as written in the Pine source
# --------------------------------------------------------------------------- #


def rolling_pop_std(x: np.ndarray, n: int) -> np.ndarray:
    """Pine `ta.stdev(x, n)` (biased / population form). NaN until n bars exist."""
    out = np.full(len(x), np.nan)
    for t in range(n - 1, len(x)):
        out[t] = np.std(x[t - n + 1 : t + 1])
    return out


@dataclass
class VaultParams:
    std_multiplier: float = 2.0
    length: int = 20
    cost_bps_per_side: float = 0.0  # the vault file models none


@dataclass
class VaultResult:
    vwap: np.ndarray
    std: np.ndarray
    upper: np.ndarray
    lower: np.ndarray
    go_long: np.ndarray
    go_short: np.ndarray
    position: np.ndarray  # position held during bar t (after the open fill)
    trades: list[Trade]


def run_vault(bars: Bars, p: VaultParams = VaultParams()) -> VaultResult:
    """Bar-close signals, next-bar-open fills (Pine strategy defaults).

    `ta.cum` starts at the first bar handed in, so the "VWAP" is anchored to
    whatever history the caller loaded. That is the point of `fig04`.

    Order interaction when a reversal entry and a `strategy.close` fire on the
    same bar is modelled as "reversal wins"; Pine's exact netting there is an
    implementation detail the vault file never pins down.
    """
    c, v, o = bars.c, bars.v, bars.o
    n = len(c)
    vwap = np.cumsum(c * v) / np.cumsum(v)
    std = rolling_pop_std(c, p.length)
    upper = vwap + p.std_multiplier * std
    lower = vwap - p.std_multiplier * std

    go_long = np.zeros(n, bool)
    go_short = np.zeros(n, bool)
    go_long[1:] = (c[1:] < lower[1:]) & (c[:-1] >= lower[:-1])
    go_short[1:] = (c[1:] > upper[1:]) & (c[:-1] <= upper[:-1])

    position = np.zeros(n, int)
    trades: list[Trade] = []
    pos = 0
    open_trade: Trade | None = None
    pending: int | None = None
    pending_signal_t = -1

    for t in range(n):
        if pending is not None and pending != pos:
            if open_trade is not None:
                open_trade.exit_t, open_trade.exit_px = t, o[t]
                open_trade.reason = "REVERSE" if pending != 0 else "VWAP_TOUCH"
                open_trade.exit_cost_bps = p.cost_bps_per_side
                trades.append(open_trade)
                open_trade = None
            if pending != 0:
                open_trade = Trade(pending, pending_signal_t, t, o[t], entry_cost_bps=p.cost_bps_per_side)
            pos = pending
        pending = None
        position[t] = pos

        target = pos
        if go_long[t]:
            target = 1
        if go_short[t]:
            target = -1
        reversing = target != pos and target != 0
        if not reversing:
            if pos > 0 and c[t] > vwap[t]:
                target = 0
            if pos < 0 and c[t] < vwap[t]:
                target = 0
        if target != pos and t + 1 < n:
            pending, pending_signal_t = target, t

    if open_trade is not None:
        trades.append(open_trade)
    return VaultResult(vwap, std, upper, lower, go_long, go_short, position, trades)


# --------------------------------------------------------------------------- #
# Paper v1 contract
# --------------------------------------------------------------------------- #


@dataclass
class V1Params:
    k_arm: float = 2.0  # stretch that arms a fade
    k_min_left: float = 1.0  # must still be at least this far from VWAP at entry
    k_kill: float = 3.5  # close beyond this z while armed or in position kills it
    mae_sigma: float = 1.25  # hard stop: adverse excursion in entry-sigma units
    arm_window: int = 10  # bars an arm stays live
    time_stop: int = 45  # bars
    cooldown: int = 10  # bars after any exit
    warmup: int = 60  # bars after session anchor before any entry
    no_entry_last: int = 60  # no new entries this close to session end
    flat_before_end: int = 15  # force flat this close to session end
    session_len: int = 1440
    sigma_floor_bps: float = 3.0
    er_len: int = 60
    er_max: float = 0.35  # Kaufman efficiency ratio ceiling
    slope_len: int = 60
    slope_max_sigma: float = 0.5  # VWAP drift over slope_len, in sigma units, tolerated against the fade
    persist_len: int = 120
    persist_max: float = 0.75  # share of recent closes on one side of VWAP that marks a one-sided session
    use_filters: bool = True
    taker_bps: float = 5.0  # paper placeholder; replace with measured venue tier + slippage
    maker_bps: float = 1.0
    blackout: tuple[tuple[int, int], ...] = ()  # (start_bar, end_bar) absolute indices


@dataclass
class V1Frame:
    vwap_prev: np.ndarray
    sigma_prev: np.ndarray
    z: np.ndarray
    er: np.ndarray
    slope_sigma: np.ndarray
    frac_above: np.ndarray
    eligible_long: np.ndarray
    eligible_short: np.ndarray


@dataclass
class V1Result:
    frame: V1Frame
    trades: list[Trade]
    events: list[tuple[int, str]] = field(default_factory=list)
    position: np.ndarray | None = None


def v1_frame(bars: Bars, p: V1Params) -> V1Frame:
    """Session-anchored VWAP and volume-weighted residual sigma, frozen at t-1.

    Every quantity used to decide at the close of bar t is computed from bars
    strictly before t, except the close of t itself (the thing being judged).
    """
    h, l, c, v, sess, minute = bars.h, bars.l, bars.c, bars.v, bars.session, bars.minute
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
        vw = spv / sv
        vwap_now[t] = vw
        sig_now[t] = np.sqrt(max(sp2v / sv - vw * vw, 0.0))

    vwap_prev = np.full(n, np.nan)
    sigma_prev = np.full(n, np.nan)
    same = np.zeros(n, bool)
    same[1:] = sess[1:] == sess[:-1]
    vwap_prev[1:] = np.where(same[1:], vwap_now[:-1], np.nan)
    floor = p.sigma_floor_bps * 1e-4 * vwap_prev
    sigma_prev[1:] = np.where(same[1:], sig_now[:-1], np.nan)
    sigma_prev = np.fmax(sigma_prev, floor)
    z = (c - vwap_prev) / sigma_prev

    er = np.full(n, np.nan)
    absd = np.abs(np.diff(c, prepend=c[0]))
    for t in range(p.er_len, n):
        path = absd[t - p.er_len + 1 : t + 1].sum()
        er[t] = abs(c[t] - c[t - p.er_len]) / path if path > 0 else 0.0

    slope_sigma = np.full(n, np.nan)
    slope_sigma[p.slope_len :] = (vwap_prev[p.slope_len :] - vwap_prev[: -p.slope_len]) / sigma_prev[p.slope_len :]

    above = (c > vwap_prev).astype(float)
    frac_above = np.full(n, np.nan)
    for t in range(n):
        lo = t - p.persist_len + 1
        while lo < t and (lo < 0 or sess[lo] != sess[t]):
            lo += 1
        if t - lo + 1 >= 30:
            frac_above[t] = above[lo : t + 1].mean()

    base = (minute >= p.warmup) & (minute < p.session_len - p.no_entry_last) & np.isfinite(z)
    for a, b in p.blackout:
        base[a:b] = False
    eligible_long = base.copy()
    eligible_short = base.copy()
    if p.use_filters:
        calm = np.nan_to_num(er, nan=1.0) < p.er_max
        slope = np.nan_to_num(slope_sigma, nan=0.0)
        frac = np.nan_to_num(frac_above, nan=0.5)
        eligible_long &= calm & (slope > -p.slope_max_sigma) & (frac > 1.0 - p.persist_max)
        eligible_short &= calm & (slope < p.slope_max_sigma) & (frac < p.persist_max)
    return V1Frame(vwap_prev, sigma_prev, z, er, slope_sigma, frac_above, eligible_long, eligible_short)


def run_v1(bars: Bars, p: V1Params = V1Params()) -> V1Result:
    f = v1_frame(bars, p)
    o, h, l, c, minute = bars.o, bars.h, bars.l, bars.c, bars.minute
    n = len(c)
    trades: list[Trade] = []
    events: list[tuple[int, str]] = []
    position = np.zeros(n, int)

    state = "FLAT"
    arm_side, arm_t = 0, -1
    cool_until = -1
    tr: Trade | None = None
    stop_px = np.nan
    pending_entry: tuple[int, int, float] | None = None  # side, signal_t, sigma at signal
    pending_exit: str | None = None

    for t in range(n):
        if pending_exit is not None and tr is not None:
            tr.exit_t, tr.exit_px, tr.reason = t, o[t], pending_exit
            tr.exit_cost_bps = p.taker_bps
            trades.append(tr)
            events.append((t, pending_exit))
            tr, pending_exit, state, cool_until = None, None, "COOLDOWN", t + p.cooldown
        if pending_entry is not None:
            side, sig_t, sig_sigma = pending_entry
            tr = Trade(side, sig_t, t, o[t], entry_cost_bps=p.taker_bps)
            stop_px = o[t] - side * p.mae_sigma * sig_sigma
            state, pending_entry = "IN_POS", None
            events.append((t, "ENTRY"))

        z = f.z[t]
        if state == "IN_POS" and tr is not None:
            position[t] = tr.side
            hit_stop = (l[t] <= stop_px) if tr.side > 0 else (h[t] >= stop_px)
            target = f.vwap_prev[t]
            hit_target = np.isfinite(target) and ((h[t] > target) if tr.side > 0 else (l[t] < target))
            if hit_stop:
                gap = (o[t] < stop_px) if tr.side > 0 else (o[t] > stop_px)
                tr.exit_t, tr.exit_px, tr.reason = t, (o[t] if gap else stop_px), "MAE_STOP"
                tr.exit_cost_bps = p.taker_bps
            elif hit_target:
                tr.exit_t, tr.exit_px, tr.reason = t, target, "TARGET_VWAP"
                tr.exit_cost_bps = p.maker_bps
            if tr.exit_t is not None:
                trades.append(tr)
                events.append((t, tr.reason))
                tr, state, cool_until = None, "COOLDOWN", t + p.cooldown
                continue
            held = t - tr.entry_t + 1
            if t + 1 < n:
                if held >= p.time_stop:
                    pending_exit = "TIME_STOP"
                elif np.isfinite(z) and tr.side * z <= -p.k_kill:
                    pending_exit = "Z_KILL"
                elif minute[t] >= p.session_len - p.flat_before_end or (
                    t + 1 < n and bars.session[t + 1] != bars.session[t]
                ):
                    pending_exit = "SESSION_FLAT"
            continue

        if state == "COOLDOWN":
            if t >= cool_until:
                state = "FLAT"
            else:
                continue

        if not np.isfinite(z):
            state = "FLAT"
            continue

        if state == "FLAT":
            if z <= -p.k_arm:
                state, arm_side, arm_t = "ARMED", 1, t
                events.append((t, "ARM_LONG"))
            elif z >= p.k_arm:
                state, arm_side, arm_t = "ARMED", -1, t
                events.append((t, "ARM_SHORT"))
            continue

        if state == "ARMED":
            sz = arm_side * z  # negative = stretched against the fade
            if bars.session[t] != bars.session[arm_t]:
                state = "FLAT"
            elif sz <= -p.k_kill:
                state = "FLAT"
                events.append((t, "DISARM_KILL"))
            elif t - arm_t > p.arm_window:
                state = "FLAT"
                events.append((t, "DISARM_EXPIRED"))
            elif sz > -p.k_arm:
                if sz <= -p.k_min_left:
                    ok = f.eligible_long[t] if arm_side > 0 else f.eligible_short[t]
                    if ok and t + 1 < n:
                        pending_entry = (arm_side, t, f.sigma_prev[t])
                        events.append((t, "SIGNAL_LONG" if arm_side > 0 else "SIGNAL_SHORT"))
                    else:
                        events.append((t, "BLOCKED_INELIGIBLE"))
                else:
                    events.append((t, "DISARM_NO_ROOM"))
                state = "FLAT"

    if tr is not None:
        trades.append(tr)
    return V1Result(f, trades, events, position)


# --------------------------------------------------------------------------- #
# Synthetic paths (educational only)
# --------------------------------------------------------------------------- #

SUBSTEPS = 12


@dataclass
class Shock:
    start: int  # minute within session
    duration: int  # minutes
    move: float  # total deterministic move in price units


def _fine_to_bars(fine: np.ndarray, vol_mult: np.ndarray, rng: np.random.Generator, session_id: int, minute0: int = 0) -> Bars:
    m = (len(fine) - 1) // SUBSTEPS
    seg = fine[: m * SUBSTEPS + 1]
    o = seg[0:-1:SUBSTEPS][:m]
    c = seg[SUBSTEPS::SUBSTEPS][:m]
    h = np.array([seg[i * SUBSTEPS : (i + 1) * SUBSTEPS + 1].max() for i in range(m)])
    l = np.array([seg[i * SUBSTEPS : (i + 1) * SUBSTEPS + 1].min() for i in range(m)])
    minute = np.arange(minute0, minute0 + m)
    u_shape = 1.0 + 0.8 * np.cos(np.linspace(0, 2 * np.pi, m)) ** 2
    rng_rel = (h - l) / np.median(h - l)
    v = 100.0 * u_shape * (0.4 + 0.6 * rng_rel) * vol_mult[:m] * rng.lognormal(0.0, 0.35, m)
    return Bars(o, h, l, c, v, np.full(m, session_id), minute)


def synth_session(
    seed: int,
    minutes: int = 600,
    p0: float = 100.0,
    mu: float | None = None,
    theta: float = 0.03,  # per-minute OU pull toward mu
    sigma: float = 0.035,  # per-minute diffusion, price units
    drift: float = 0.0,  # per-minute drift applied to mu (trend days)
    shocks: tuple[Shock, ...] = (),
    shock_footprint: float = 0.0,  # fraction of each shock that permanently moves the OU anchor
    session_id: int = 0,
) -> Bars:
    rng = np.random.default_rng(seed)
    dt = 1.0 / SUBSTEPS
    fine = np.empty(minutes * SUBSTEPS + 1)
    fine[0] = p0
    anchor = p0 if mu is None else mu
    shock_drift = np.zeros(minutes)
    vol_mult = np.ones(minutes)
    for s in shocks:
        shock_drift[s.start : s.start + s.duration] += s.move / s.duration
        vol_mult[s.start : s.start + s.duration] *= 3.0
    for i in range(1, len(fine)):
        minute = (i - 1) // SUBSTEPS
        anchor += drift * dt
        pull = -theta * (fine[i - 1] - anchor) * dt
        fine[i] = fine[i - 1] + pull + shock_drift[minute] * dt + sigma * np.sqrt(dt) * rng.standard_normal()
        if shock_drift[minute] != 0.0:
            anchor += shock_footprint * shock_drift[minute] * dt
    return _fine_to_bars(fine, vol_mult, rng, session_id)


def concat(sessions: list[Bars]) -> Bars:
    return Bars(
        *(np.concatenate([getattr(b, k) for b in sessions]) for k in ("o", "h", "l", "c", "v", "session", "minute"))
    )


def synth_multiday(seed: int, days: int = 5, minutes: int = 1440, p0: float = 100.0, day_drifts=None) -> Bars:
    rng = np.random.default_rng(seed)
    out = []
    px = p0
    drifts = day_drifts if day_drifts is not None else rng.normal(0.0, 0.0015, days)
    for d in range(days):
        b = synth_session(
            seed=seed * 100 + d,
            minutes=minutes,
            p0=px,
            theta=0.01,
            sigma=0.03,
            drift=drifts[d],
            session_id=d,
        )
        out.append(b)
        px = b.c[-1]
    return concat(out)
