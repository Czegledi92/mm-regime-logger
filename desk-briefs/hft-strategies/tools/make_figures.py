"""Render the educational figures for the VWAP SD mean-reversion teardown.

PAPER / RESEARCH ONLY. Every price path here is synthetic and seeded. Nothing
here is a backtest and nothing here is evidence of edge.

    python3 desk-briefs/hft-strategies/tools/make_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vwap_sd_mr_research import (  # noqa: E402
    Bars,
    Shock,
    Trade,
    V1Params,
    VaultParams,
    run_v1,
    run_vault,
    synth_multiday,
    synth_session,
)

OUT = Path(__file__).resolve().parent.parent / "figures"

PRICE = "#2b2b2b"
VWAP = "#1f5fbf"
UPPER = "#c0392b"
LOWER = "#1e8449"
KILL = "#7d3c98"
NEUTRAL = "#7f8c8d"
SHADE_BAD = "#f5b7b1"
SHADE_GOOD = "#d5f5e3"
TAG = "SYNTHETIC / EDUCATIONAL: seeded simulated 1m bars, not historical data, not a backtest"

RANGE_SEED = 1
RANGE_SHOCKS = (Shock(170, 6, -1.0), Shock(400, 6, 1.0))
TREND_SEED = 1
SESSION_MIN = 600

plt.rcParams.update(
    {
        "figure.dpi": 110,
        "savefig.dpi": 160,
        "font.size": 9.5,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "legend.frameon": False,
        "legend.fontsize": 8.5,
    }
)


def tag(fig, text: str = TAG) -> None:
    fig.text(0.5, 0.005, text, ha="center", va="bottom", fontsize=8, color="#a93226", style="italic")


def range_session() -> Bars:
    return synth_session(RANGE_SEED, minutes=SESSION_MIN, theta=0.04, shocks=RANGE_SHOCKS)


def trend_session() -> Bars:
    return synth_session(
        TREND_SEED, minutes=SESSION_MIN, theta=0.05, drift=0.005, shocks=(Shock(150, 5, 0.6),), shock_footprint=1.0
    )


def equity_bps(bars: Bars, trades: list[Trade]) -> np.ndarray:
    eq = np.zeros(len(bars))
    for tr in trades:
        end = tr.exit_t if tr.exit_t is not None else len(bars)
        mtm = tr.side * (bars.c[tr.entry_t : end] / tr.entry_px - 1.0) * 1e4 - tr.entry_cost_bps
        eq[tr.entry_t : end] += mtm
        if tr.exit_t is not None:
            eq[tr.exit_t :] += tr.net_bps
    return eq


def draw_price(ax, bars: Bars, x0: int = 0, lw: float = 0.9) -> np.ndarray:
    x = np.arange(len(bars)) + x0
    ax.vlines(x, bars.l, bars.h, color="#b3b6b7", lw=0.6, zorder=1)
    ax.plot(x, bars.c, color=PRICE, lw=lw, zorder=2, label="close")
    return x


def mark_vault_trades(ax, bars: Bars, trades: list[Trade], window=None, annotate=False):
    for tr in trades:
        if window and not (window[0] <= tr.entry_t <= window[1]):
            continue
        col = LOWER if tr.side > 0 else UPPER
        ax.scatter(tr.entry_t, tr.entry_px, marker="^" if tr.side > 0 else "v", s=70, color=col, zorder=5, edgecolor="k", lw=0.5)
        ax.scatter(tr.signal_t, bars.c[tr.signal_t], marker="o", s=22, facecolor="none", edgecolor=col, zorder=5, lw=1.0)
        if tr.exit_t is not None:
            ax.scatter(tr.exit_t, tr.exit_px, marker="X", s=60, color="k", zorder=5)
            ax.plot([tr.entry_t, tr.exit_t], [tr.entry_px, tr.exit_px], color=col, lw=1.2, ls="--", zorder=4)


# --------------------------------------------------------------------------- #
# fig01: state machines
# --------------------------------------------------------------------------- #


def _box(ax, xy, text, w=1.9, h=0.62, fc="#ffffff", ec="#34495e", fs=9, bold=False):
    x, y = xy
    ax.add_patch(
        FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.04,rounding_size=0.12", fc=fc, ec=ec, lw=1.3)
    )
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, weight="bold" if bold else "normal")


def _arrow(ax, a, b, text="", color="#34495e", rad=0.0, fs=7.8, offset=(0, 0), ls="-"):
    ax.add_patch(
        FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=11, color=color, lw=1.2, connectionstyle=f"arc3,rad={rad}", ls=ls)
    )
    if text:
        mx, my = (a[0] + b[0]) / 2 + offset[0], (a[1] + b[1]) / 2 + offset[1]
        ax.text(mx, my, text, ha="center", va="center", fontsize=fs, color=color,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))


def fig01_state_machines():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14.5, 6.6), gridspec_kw={"width_ratios": [1, 1.35]})
    for ax in (a1, a2):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 8)
        ax.axis("off")

    a1.set_title("Vault Pine as written: 3 states, no kills")
    _box(a1, (5, 4), "FLAT", fc="#ecf0f1", bold=True)
    _box(a1, (2, 6.6), "LONG", fc=SHADE_GOOD, bold=True)
    _box(a1, (8, 6.6), "SHORT", fc=SHADE_BAD, bold=True)
    _arrow(a1, (4.5, 4.35), (2.4, 6.25), "crossunder(close, VWAP-2*stdev(close,20))", color=LOWER, rad=-0.15, offset=(-0.9, -0.35))
    _arrow(a1, (2.5, 6.25), (4.6, 4.35), "close > VWAP\n(exit long)", rad=-0.15, offset=(-0.15, 0.45))
    _arrow(a1, (5.5, 4.35), (7.6, 6.25), "crossover(close, VWAP+2*stdev)", color=UPPER, rad=0.15, offset=(0.9, -0.35))
    _arrow(a1, (7.5, 6.25), (5.4, 4.35), "close < VWAP\n(exit short)", rad=0.15, offset=(0.15, 0.45))
    _arrow(a1, (2.95, 6.75), (7.05, 6.75), "crossover(upper): reverse", color=UPPER, rad=-0.25, offset=(0, 0.85))
    _arrow(a1, (7.05, 6.45), (2.95, 6.45), "crossunder(lower): reverse", color=LOWER, rad=-0.25, offset=(0, -0.3))
    defects = [
        "VWAP = cum(close*vol)/cum(vol) over ALL loaded history (no session reset)",
        "Band width = stdev of CLOSE about its own 20-bar mean, not distance from VWAP",
        "Entry on the pierce bar itself: buys into the impulse, no confirmation",
        "No stop, no time stop, no session flat: a trend day holds the loser indefinitely",
        "Reversal on opposite band: can flip long->short with no flat check",
        "No fees, slippage, or latency; fills at next open assumed free",
    ]
    for i, d in enumerate(defects):
        a1.text(0.2, 2.55 - i * 0.42, f"x  {d}", fontsize=8.3, color="#922b21", va="center")
    a1.text(0.2, 2.95, "What is missing:", fontsize=9, weight="bold", color="#922b21")

    a2.set_title("Paper v1 contract: armed fade with explicit kills")
    _box(a2, (1.4, 4), "FLAT", fc="#ecf0f1", bold=True, w=1.6)
    _box(a2, (4.3, 4), "ARMED\n|z| >= k_arm", fc="#fef9e7", w=1.9, h=0.85)
    _box(a2, (7.4, 4), "IN POSITION\n(one at a time)", fc="#eaf2f8", w=2.1, h=0.85)
    _box(a2, (7.4, 1.4), "COOLDOWN\nN bars", fc="#f4ecf7", w=1.9, h=0.8)
    _box(a2, (4.3, 7.0), "Eligibility gate\nwarmup, not last hour, no event blackout,\nER < max, VWAP slope & side-persistence OK", fc="#fdfefe", ec=NEUTRAL, w=4.4, h=1.0, fs=8)
    _arrow(a2, (2.2, 4.1), (3.35, 4.1), "z <= -k_arm\nor z >= +k_arm", offset=(0, 0.45))
    _arrow(a2, (3.35, 3.85), (2.2, 3.85), "expired / blown\nthrough k_kill / no room\n/ ineligible", color=NEUTRAL, offset=(0, -0.65), fs=7.4)
    _arrow(a2, (5.25, 4.0), (6.35, 4.0), "re-entry close\ninside k_arm with\n|z| >= k_min_left", color="#1f618d", offset=(0, 0.62), fs=7.4)
    _arrow(a2, (4.3, 6.5), (4.3, 4.45), "", color=NEUTRAL, ls="--")
    exits = [
        "target: limit at frozen VWAP(t-1) (maker)",
        "MAE stop: entry -/+ mae_sigma * sigma_entry",
        "z kill: close beyond k_kill",
        "time stop: held >= T bars",
        "session flat / event blackout",
    ]
    _arrow(a2, (7.4, 3.55), (7.4, 1.8), "", color=KILL)
    for i, e in enumerate(exits):
        a2.text(7.6, 3.2 - i * 0.3, e, fontsize=7.6, color=KILL, va="center")
    _arrow(a2, (6.45, 1.4), (1.4, 3.65), "cooldown elapsed", color=NEUTRAL, rad=-0.25, offset=(-0.4, -0.45))
    a2.text(0.1, 0.35, "All decision inputs at bar t use VWAP and sigma frozen at t-1 within the current session; "
            "z = (close_t - VWAP_{t-1}) / sigma_{t-1}.", fontsize=8.2, color="#1f618d")
    fig.text(0.5, 0.005, "Diagram only. Thresholds are placeholders to be set by pre-registered research, not tuned on this figure.",
             ha="center", fontsize=8, color="#a93226", style="italic")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / "fig01_state_machines.png")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# fig02: canonical fade episodes, vault geometry
# --------------------------------------------------------------------------- #


def fig02_vault_fade_episodes():
    b = range_session()
    vr = run_vault(b)
    fig = plt.figure(figsize=(14, 8.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.1], hspace=0.32, wspace=0.14)
    ax = fig.add_subplot(gs[0, :])
    x = draw_price(ax, b)
    ax.plot(x, vr.vwap, color=VWAP, lw=1.8, label="VWAP (cum from first loaded bar)")
    ax.plot(x, vr.upper, color=UPPER, lw=1.0, label="VWAP + 2*stdev(close,20)")
    ax.plot(x, vr.lower, color=LOWER, lw=1.0, label="VWAP - 2*stdev(close,20)")
    mark_vault_trades(ax, b, vr.trades)
    for (lo, hi), lab in (((150, 235), "long episode"), ((385, 475), "short episode")):
        ax.axvspan(lo, hi, color="#f9e79f", alpha=0.35, zorder=0)
        ax.text((lo + hi) / 2, ax.get_ylim()[1], lab, ha="center", va="top", fontsize=8.5, weight="bold")
    n = len(vr.trades)
    ax.set_title(f"Vault logic on a mean-reverting synthetic session: {n} trades in 600 bars, costs = 0 (as in the vault file)")
    ax.set_xlabel("minutes from session anchor")
    ax.set_ylabel("price (synthetic index)")
    ax.legend(loc="lower left", ncol=4)

    def zoom(axz, lo, hi, side):
        s = slice(lo, hi)
        xs = np.arange(lo, hi)
        axz.vlines(xs, b.l[s], b.h[s], color="#b3b6b7", lw=0.8)
        axz.plot(xs, b.c[s], color=PRICE, lw=1.1)
        axz.plot(xs, vr.vwap[s], color=VWAP, lw=2.0)
        axz.plot(xs, vr.upper[s], color=UPPER, lw=1.0)
        axz.plot(xs, vr.lower[s], color=LOWER, lw=1.0)
        axz.fill_between(xs, vr.lower[s], vr.upper[s], color=VWAP, alpha=0.05)
        tr = next(t for t in vr.trades if lo <= t.entry_t <= hi and t.side == side)
        mark_vault_trades(axz, b, [tr])
        col = LOWER if side > 0 else UPPER
        verb = "under lower" if side > 0 else "over upper"
        ext = (np.min(b.l[tr.entry_t : tr.exit_t]) if side > 0 else np.max(b.h[tr.entry_t : tr.exit_t]))
        mae = side * (ext / tr.entry_px - 1) * 1e4
        pos = {+1: ((0.42, 0.05), (0.58, 0.22), (0.38, 0.90)), -1: ((0.30, 0.93), (0.40, 0.78), (0.45, 0.10))}[side]
        box = dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85)
        axz.annotate(f"1) close crosses {verb} band (signal on bar close)", xy=(tr.signal_t, b.c[tr.signal_t]),
                     xytext=pos[0], textcoords="axes fraction", fontsize=8.3, color=col, bbox=box,
                     arrowprops=dict(arrowstyle="->", color=col))
        axz.annotate("2) fill at next open: still inside the impulse", xy=(tr.entry_t, tr.entry_px),
                     xytext=pos[1], textcoords="axes fraction", fontsize=8.3, color=col, bbox=box,
                     arrowprops=dict(arrowstyle="->", color=col))
        axz.annotate(f"3) close back {'above' if side > 0 else 'below'} VWAP -> exit next open\n"
                     f"    gross {tr.gross_bps:+.1f} bps, MAE {mae:+.1f} bps, held {tr.exit_t - tr.entry_t} bars",
                     xy=(tr.exit_t, tr.exit_px), xytext=pos[2], textcoords="axes fraction", fontsize=8.3, bbox=box,
                     arrowprops=dict(arrowstyle="->", color="k"))
        axz.set_title(f"{'Long' if side > 0 else 'Short'} fade: pierce {'lower' if side > 0 else 'upper'} band, revert to VWAP")
        axz.set_xlabel("minutes from session anchor")

    zoom(fig.add_subplot(gs[1, 0]), 150, 235, +1)
    zoom(fig.add_subplot(gs[1, 1]), 385, 475, -1)
    tag(fig)
    fig.savefig(OUT / "fig02_vault_fade_episodes.png", bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# fig03: trend failure
# --------------------------------------------------------------------------- #


def fig03_trend_failure():
    b = trend_session()
    vr = run_vault(b)
    p = V1Params(session_len=SESSION_MIN)
    r_on = run_v1(b, p)
    r_off = run_v1(b, V1Params(session_len=SESSION_MIN, use_filters=False))
    f = r_off.frame
    x = np.arange(len(b))

    fig, axes = plt.subplots(3, 1, figsize=(13.5, 11), sharex=True, gridspec_kw={"height_ratios": [1.25, 1.25, 0.9]})
    ax = axes[0]
    draw_price(ax, b)
    ax.plot(x, vr.vwap, color=VWAP, lw=1.8, label="vault VWAP")
    ax.plot(x, vr.upper, color=UPPER, lw=1.0, label="vault upper band")
    ax.plot(x, vr.lower, color=LOWER, lw=1.0, label="vault lower band")
    mark_vault_trades(ax, b, vr.trades)
    stuck = [t for t in vr.trades if t.exit_t is None]
    if stuck:
        tr = stuck[0]
        ax.fill_between(x[tr.entry_t :], tr.entry_px, b.c[tr.entry_t :], where=b.c[tr.entry_t :] > tr.entry_px, color=SHADE_BAD, alpha=0.7, zorder=0)
        mtm = -(b.c[-1] / tr.entry_px - 1) * 1e4
        ax.annotate(f"short opened on upper-band cross at t={tr.entry_t}; close never returns below VWAP\n"
                    f"-> still open at session end, MTM {mtm:+.0f} bps. No stop, no time stop, no session flat.",
                    xy=(tr.entry_t, tr.entry_px), xytext=(0.22, 0.80), textcoords="axes fraction", fontsize=8.8, color=UPPER,
                    bbox=dict(fc="white", ec="none", alpha=0.85), arrowprops=dict(arrowstyle="->", color=UPPER))
    ax.annotate("price lives above the upper band for hours: the band is centred on a lagging VWAP and its\n"
                "width is 20-bar close noise, so 'outside 2 sigma' becomes the normal state, not an extreme",
                xy=(450, vr.upper[450]), xytext=(0.42, 0.12), textcoords="axes fraction", fontsize=8.5, color="#6e2c00",
                bbox=dict(fc="white", ec="none", alpha=0.85), arrowprops=dict(arrowstyle="->", color="#6e2c00"))
    ax.set_title("Failure case: vault logic on a synthetic grind-up trend day (mean-reversion assumption false)")
    ax.legend(loc="upper left", ncol=4)
    ax.set_ylabel("price (synthetic index)")

    ax = axes[1]
    draw_price(ax, b)
    ax.plot(x, f.vwap_prev, color=VWAP, lw=1.8, label="session VWAP, frozen t-1")
    for k, ls, lab in ((2.0, "-", "+/-2 sigma_resid (arm)"), (3.5, ":", "+/-3.5 sigma_resid (kill)")):
        ax.plot(x, f.vwap_prev + k * f.sigma_prev, color=UPPER, lw=1.0, ls=ls, label=lab)
        ax.plot(x, f.vwap_prev - k * f.sigma_prev, color=LOWER, lw=1.0, ls=ls)
    for tr in r_off.trades:
        ax.scatter(tr.entry_t, tr.entry_px, marker="v", s=60, color=UPPER, edgecolor="k", lw=0.5, zorder=5)
        ax.scatter(tr.exit_t, tr.exit_px, marker="X", s=55, color=KILL, zorder=5)
        ax.plot([tr.entry_t, tr.exit_t], [tr.entry_px, tr.exit_px], color=KILL, lw=1.2, ls="--")
    reasons = ", ".join(f"{t.reason} {t.net_bps:+.0f}" for t in r_off.trades)
    ax.plot([], [], color=KILL, ls="--", marker="X", label=f"v1 filters OFF: {len(r_off.trades)} shorts ({reasons} bps)")
    ax.annotate("residual sigma grows with the trend, so the +2 sigma arm band chases\n"
                "price upward and every fresh high re-arms another short fade",
                xy=(300, (f.vwap_prev + 2 * f.sigma_prev)[300]), xytext=(0.45, 0.30), textcoords="axes fraction",
                fontsize=8.5, color="#6e2c00", bbox=dict(fc="white", ec="none", alpha=0.85),
                arrowprops=dict(arrowstyle="->", color="#6e2c00"))
    blocked = [t for t, e in r_on.events if e == "BLOCKED_INELIGIBLE"]
    ax.scatter(blocked, b.c[blocked] + 0.25, marker="s", s=22, color=NEUTRAL, zorder=5,
               label=f"v1 filters ON: fade refused by warmup/filters ({len(blocked)}x); {len(r_on.trades)} trade(s) taken")
    ax.set_title("Paper v1 on the same bars. Filters OFF: kills cap each loss. Filters ON: grey squares = fades refused")
    ax.legend(loc="upper left", ncol=1)
    ax.set_ylabel("price (synthetic index)")

    ax = axes[2]
    ax.plot(x, equity_bps(b, vr.trades), color=UPPER, lw=1.8, label="vault (no costs, no kills)")
    ax.plot(x, equity_bps(b, r_off.trades), color=KILL, lw=1.6, label="v1 filters OFF (net of paper costs)")
    ax.plot(x, equity_bps(b, r_on.trades), color="#1f618d", lw=1.6, label="v1 filters ON (net of paper costs)")
    ax.axhline(0, color="k", lw=0.7)
    ax.set_ylabel("cumulative P&L, bps of 1 unit\n(realised + open MTM)")
    ax.set_xlabel("minutes from session anchor")
    ax.set_title("Same session, running P&L. One synthetic day: illustrates loss shape only, says nothing about expectancy")
    ax.legend(loc="lower left")
    tag(fig)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(OUT / "fig03_trend_failure.png")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# fig04: lifetime cumulative VWAP depends on the history you load
# --------------------------------------------------------------------------- #


def multiday() -> Bars:
    return synth_multiday(7, days=5, day_drifts=np.array([0.0004, 0.0012, 0.0010, -0.0006, 0.0011]))


def fig04_lifetime_vs_session_vwap():
    b = multiday()
    day = 1440
    va = run_vault(b)
    b_late = b.slice(2 * day)
    vb = run_vault(b_late)
    f = run_v1(b, V1Params(session_len=day)).frame
    x = np.arange(len(b))

    fig, axes = plt.subplots(2, 1, figsize=(13.5, 8.2), sharex=True, gridspec_kw={"height_ratios": [1.6, 0.8]})
    ax = axes[0]
    ax.plot(x, b.c, color=PRICE, lw=0.7, label="close")
    ax.plot(x, va.vwap, color=VWAP, lw=2.0, label="vault VWAP, history loaded from day 0 (A)")
    ax.plot(x[2 * day :], vb.vwap, color="#e67e22", lw=2.0, label="vault VWAP, history loaded from day 2 (B)")
    sv = f.vwap_prev.copy()
    ax.plot(x, sv, color="#17a589", lw=1.2, ls="--", label="session VWAP (resets each 00:00 anchor)")
    for d in range(1, 5):
        ax.axvline(d * day, color=NEUTRAL, lw=0.8, ls=":")
    ax.set_title("Lifetime cum VWAP is anchored to wherever the data starts: same bars, two different references")
    ax.set_ylabel("price (synthetic index)")
    ax.legend(loc="upper left")
    i = 3 * day + 700
    ax.annotate(f"same bar, two 'VWAPs': A={va.vwap[i]:.2f}, B={vb.vwap[i - 2 * day]:.2f}\n"
                f"session VWAP={sv[i]:.2f}", xy=(i, va.vwap[i]), xytext=(i - 1500, va.vwap[i] + 2.2), fontsize=8.8,
                arrowprops=dict(arrowstyle="->", color=VWAP))

    ax = axes[1]
    pa = va.position[2 * day :]
    pb = vb.position
    ax.step(x[2 * day :], pa + 0.06, where="post", color=VWAP, lw=2.2, label="position under history A")
    ax.step(x[2 * day :], pb - 0.06, where="post", color="#e67e22", lw=1.1, label="position under history B")
    disagree = np.mean(pa != pb) * 100
    ax.set_yticks([-1, 0, 1], ["short", "flat", "long"])
    ax.set_title(f"Vault position on identical bars (days 2-4): histories disagree on {disagree:.0f}% of bars")
    ax.set_xlabel("minutes since first bar (5 synthetic 24h sessions)")
    ax.legend(loc="lower left", ncol=2)
    ax.set_xlim(0, len(b))
    tag(fig)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(OUT / "fig04_lifetime_vs_session_vwap.png")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# fig05: the dispersion object
# --------------------------------------------------------------------------- #


def fig05_dispersion_object():
    b = multiday()
    va = run_vault(b)
    f = run_v1(b, V1Params(session_len=1440)).frame
    z_vault = (b.c - va.vwap) / va.std
    z_v1 = f.z
    ok = np.isfinite(z_vault) & np.isfinite(z_v1) & (b.minute >= 60)

    r = range_session()
    vr = run_vault(r)
    fr = run_v1(r, V1Params(session_len=SESSION_MIN)).frame

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5.6), gridspec_kw={"width_ratios": [1, 1.25]})
    bins = np.linspace(-12, 12, 121)
    zv = np.clip(z_vault[ok], -12, 12)
    zr = np.clip(z_v1[ok], -12, 12)
    a1.hist(zv, bins=bins, color=UPPER, alpha=0.55, label="vault: (close - lifetime VWAP) / stdev(close,20)")
    a1.hist(zr, bins=bins, color=VWAP, alpha=0.55, label="v1: (close - session VWAP_{t-1}) / sigma_resid_{t-1}")
    for k in (-2, 2):
        a1.axvline(k, color="k", lw=0.8, ls="--")
    pv = np.mean(np.abs(z_vault[ok]) > 2) * 100
    pr = np.mean(np.abs(z_v1[ok]) > 2) * 100
    a1.set_yscale("log")
    a1.set_xlabel("z (clipped to +/-12)")
    a1.set_ylabel("bar count (log)")
    a1.set_title("What a '2-sigma band' means depends on the sigma")
    a1.text(0.02, 0.97, f"bars outside +/-2:\n  vault z: {pv:.0f}%\n  v1 z:    {pr:.0f}%\n(5 synthetic days)", transform=a1.transAxes,
            va="top", fontsize=9, family="monospace", bbox=dict(fc="white", ec="#bbb"))
    a1.legend(loc="upper right", fontsize=7.8)

    lo, hi = 150, 225
    xs = np.arange(lo, hi)
    s = slice(lo, hi)
    a2.plot(xs, vr.std[s] * 2, color=UPPER, lw=1.8, label="vault half-width: 2*stdev(close,20)")
    a2.plot(xs, fr.sigma_prev[s] * 2, color=VWAP, lw=1.8, label="v1 half-width: 2*sigma_resid (session, VW, t-1)")
    a2.plot(xs, np.abs(r.c[s] - vr.vwap[s]), color=PRICE, lw=1.0, label="|close - VWAP| (what the band is compared to)")
    a2.axvspan(170, 176, color="#f9e79f", alpha=0.6)
    a2.text(173, a2.get_ylim()[1] * 0.97, "impulse\nbars", ha="center", va="top", fontsize=8)
    a2.axvspan(190, 196, color="#d6eaf8", alpha=0.6)
    a2.annotate("impulse bars roll out of the 20-bar window:\nvault band snaps narrow regardless of price",
                xy=(194, vr.std[194] * 2), xytext=(198, vr.std[194] * 2 + 0.35), fontsize=8.3,
                arrowprops=dict(arrowstyle="->", color=UPPER))
    a2.annotate("the pierce bar widens its own band\n(current close is inside stdev window)", xy=(172, vr.std[172] * 2),
                xytext=(150, vr.std[172] * 2 + 0.25), fontsize=8.3, arrowprops=dict(arrowstyle="->", color=UPPER))
    a2.set_xlabel("minutes from session anchor (range session, down impulse)")
    a2.set_ylabel("price units")
    a2.set_title("Band half-width around an impulse: local close-vol vs residual-from-VWAP")
    a2.legend(loc="upper right", fontsize=7.8)
    tag(fig)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / "fig05_dispersion_object.png")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# fig06: cost hurdle (analytic, no data)
# --------------------------------------------------------------------------- #


def fig06_cost_hurdle():
    sigma_bps = np.linspace(2, 40, 300)
    gain_mult, loss_mult = 1.5, 1.25  # entry ~ -1.5 sigma from VWAP after re-entry; MAE stop 1.25 sigma_entry
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    for c, col, lab in ((2, "#1e8449", "2 bps RT (maker in & out, optimistic)"),
                        (6, "#d68910", "6 bps RT (taker in, maker out)"),
                        (10, "#c0392b", "10 bps RT (taker both sides)"),
                        (14, "#7b241c", "14 bps RT (taker + 2 bps slippage per side)")):
        g = gain_mult * sigma_bps
        l = loss_mult * sigma_bps
        p = (l + c) / (g + l)
        ax.plot(sigma_bps, p * 100, color=col, lw=2, label=lab)
    ax.axhline(100 * loss_mult / (gain_mult + loss_mult), color="k", lw=0.8, ls="--")
    ax.text(39.5, 100 * loss_mult / (gain_mult + loss_mult) - 2.5, "zero-cost breakeven", ha="right", fontsize=8.5)
    ax.set_ylim(35, 100)
    ax.set_xlabel("residual sigma at entry (bps of price): measure this on your venue, do not assume it")
    ax.set_ylabel("required hit rate to reach VWAP before the stop (%)")
    ax.set_title("Breakeven hit rate, target = 1.5 sigma to VWAP, stop = 1.25 sigma: p* = (L + c) / (G + L)")
    ax.legend(loc="upper right")
    ax.text(0.01, 0.03, "Analytic only. Ignores time-stop exits (partial gains/losses), funding, and adverse selection on maker fills.\n"
            "Vault logic has no stop, so L is unbounded and p* is undefined. That is itself the finding.",
            transform=ax.transAxes, fontsize=8.2, color="#555")
    fig.tight_layout()
    fig.savefig(OUT / "fig06_cost_hurdle.png")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# fig07: v1 geometry on the canonical range session
# --------------------------------------------------------------------------- #


def fig07_v1_episodes():
    b = range_session()
    p = V1Params(session_len=SESSION_MIN)
    r = run_v1(b, p)
    f = r.frame
    x = np.arange(len(b))
    fig = plt.figure(figsize=(14, 8.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.1], hspace=0.32, wspace=0.14)
    ax = fig.add_subplot(gs[0, :])
    draw_price(ax, b)

    def bands(axx, s):
        xs = x[s]
        axx.plot(xs, f.vwap_prev[s], color=VWAP, lw=1.9, label="session VWAP, frozen t-1")
        axx.plot(xs, (f.vwap_prev + p.k_arm * f.sigma_prev)[s], color=UPPER, lw=1.0, label=f"+/-{p.k_arm:g} sigma_resid (arm)")
        axx.plot(xs, (f.vwap_prev - p.k_arm * f.sigma_prev)[s], color=LOWER, lw=1.0)
        axx.plot(xs, (f.vwap_prev + p.k_kill * f.sigma_prev)[s], color=KILL, lw=0.9, ls=":", label=f"+/-{p.k_kill:g} sigma_resid (kill)")
        axx.plot(xs, (f.vwap_prev - p.k_kill * f.sigma_prev)[s], color=KILL, lw=0.9, ls=":")
        inel = ~(f.eligible_long | f.eligible_short)
        axx.fill_between(xs, axx.get_ylim()[0] if False else np.nanmin(b.l) - 0.2, np.nanmax(b.h) + 0.2, where=inel[s],
                         color="#d5d8dc", alpha=0.35, step="mid", zorder=0, label="no new entries (warmup/last hour/filters)")

    bands(ax, slice(None))

    def mark(axx, window=None):
        for tr in r.trades:
            if window and not (window[0] <= tr.entry_t <= window[1]):
                continue
            col = LOWER if tr.side > 0 else UPPER
            axx.scatter(tr.entry_t, tr.entry_px, marker="^" if tr.side > 0 else "v", s=70, color=col, edgecolor="k", lw=0.5, zorder=6)
            ec = "k" if tr.reason == "TARGET_VWAP" else KILL
            axx.scatter(tr.exit_t, tr.exit_px, marker="X", s=60, color=ec, zorder=6)
            axx.plot([tr.entry_t, tr.exit_t], [tr.entry_px, tr.exit_px], color=col, ls="--", lw=1.2)
        arms = [(t, e) for t, e in r.events if e.startswith("ARM") and (not window or window[0] <= t <= window[1])]
        for t, e in arms:
            col = LOWER if e == "ARM_LONG" else UPPER
            axx.scatter(t, b.c[t], marker="o", s=26, facecolor="none", edgecolor=col, lw=1.1, zorder=6)

    mark(ax)
    ax.set_title(f"Paper v1 on the same synthetic session as fig02: {len(r.trades)} trades "
                 f"({', '.join(sorted({t.reason for t in r.trades}))}), net of placeholder costs")
    ax.set_xlabel("minutes from session anchor")
    ax.set_ylabel("price (synthetic index)")
    lo_y, hi_y = ax.get_ylim()
    ax.set_ylim(lo_y - 0.25 * (hi_y - lo_y), hi_y)
    ax.legend(loc="lower left", ncol=3)

    def zoom(axz, lo, hi, side):
        s = slice(lo, hi)
        draw_price(axz, b.slice(lo, hi), x0=lo, lw=1.1)
        bands(axz, s)
        mark(axz, (lo, hi))
        tr = next(t for t in r.trades if lo <= t.entry_t <= hi and t.side == side)
        arm_t = max(t for t, e in r.events if e == ("ARM_LONG" if side > 0 else "ARM_SHORT") and t <= tr.signal_t)
        col = LOWER if side > 0 else UPPER
        span = np.nanmax(b.h[s]) - np.nanmin(b.l[s])
        pos = {+1: ((0.30, 0.06), (0.60, 0.18), (0.52, 0.90)), -1: ((0.26, 0.93), (0.45, 0.72), (0.38, 0.08))}[side]
        box = dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85)
        axz.annotate("1) close beyond 2 sigma: ARM only (no order yet)", xy=(arm_t, b.c[arm_t]),
                     xytext=pos[0], textcoords="axes fraction", fontsize=8.3, color=col, bbox=box,
                     arrowprops=dict(arrowstyle="->", color=col))
        axz.annotate(f"2) close back inside with z={f.z[tr.signal_t]:+.2f}\n    -> enter next open; MAE stop set",
                     xy=(tr.entry_t, tr.entry_px), xytext=pos[1], textcoords="axes fraction", fontsize=8.3,
                     color=col, bbox=box, arrowprops=dict(arrowstyle="->", color=col))
        axz.annotate(f"3) {tr.reason}: net {tr.net_bps:+.1f} bps\n    held {tr.exit_t - tr.entry_t} bars (time stop {p.time_stop})",
                     xy=(tr.exit_t, tr.exit_px), xytext=pos[2], textcoords="axes fraction", fontsize=8.3, bbox=box,
                     arrowprops=dict(arrowstyle="->", color="k"))
        axz.set_ylim(np.nanmin(b.l[s]) - 0.15 * span, np.nanmax(b.h[s]) + 0.15 * span)
        axz.set_xlim(lo, hi)
        axz.set_title(f"{'Long' if side > 0 else 'Short'} fade under v1: arm, confirm re-entry, exit at frozen VWAP")
        axz.set_xlabel("minutes from session anchor")

    zoom(fig.add_subplot(gs[1, 0]), 150, 235, +1)
    zoom(fig.add_subplot(gs[1, 1]), 385, 475, -1)
    tag(fig)
    fig.savefig(OUT / "fig07_v1_fade_episodes.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig01_state_machines()
    fig02_vault_fade_episodes()
    fig03_trend_failure()
    fig04_lifetime_vs_session_vwap()
    fig05_dispersion_object()
    fig06_cost_hurdle()
    fig07_v1_episodes()
    for pth in sorted(OUT.glob("*.png")):
        print(pth.relative_to(OUT.parent.parent.parent))


if __name__ == "__main__":
    main()
