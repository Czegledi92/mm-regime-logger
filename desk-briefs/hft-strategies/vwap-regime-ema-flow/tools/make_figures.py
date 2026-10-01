"""Render the educational figures for the VWAP regime + EMA ribbon flow packet.

PAPER / RESEARCH ONLY. Every price path here is synthetic and seeded. Nothing
here is a backtest and nothing here is evidence of edge.

    python3 desk-briefs/hft-strategies/vwap-regime-ema-flow/tools/make_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vwap_regime_flow import (  # noqa: E402
    SESSION_BARS,
    Bars,
    InventoryParams,
    PerpParams,
    RegimeParams,
    RibbonFrame,
    RibbonParams,
    Seg,
    cell,
    last_session,
    markouts,
    ribbon,
    run_inventory,
    run_perp,
    run_side_follow,
    synth_path,
    vwap_regime,
)

OUT = Path(__file__).resolve().parent.parent / "figures"
D = SESSION_BARS

PRICE = "#2b2b2b"
VWAP = "#1f5fbf"
E21, E50, E100 = "#e67e22", "#8e44ad", "#117a65"
ABOVE, BELOW, UNDEF = "#d5f5e3", "#fadbd8", "#eeeeee"
LONG, SHORT = "#1e8449", "#c0392b"
RIB = {2: "#27ae60", 1: "#a9dfbf", 0: "#bdc3c7", -1: "#f5b7b1", -2: "#c0392b"}
CELL = {"AGREE": "#27ae60", "WEAK": "#f7dc6f", "TANGLED": "#bdc3c7", "CONFLICT": "#8e44ad", "UNDEFINED": "#eeeeee"}
TAG = "SYNTHETIC / EDUCATIONAL: seeded simulated 5m bars, not historical data, not a backtest"

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
    fig.text(0.5, 0.004, text, ha="center", va="bottom", fontsize=8, color="#a93226", style="italic")


# --------------------------------------------------------------------------- #
# Scenarios (all seeded; prior sessions exist only to warm the EMAs)
# --------------------------------------------------------------------------- #


def bull_day(seed: int = 5) -> Bars:
    return synth_path(seed, [Seg(2 * D, 1.0, 10, 0.1), Seg(30, -3, 10, 0.1), Seg(D - 30, 2.0, 10, 0.1)])


def bear_day(seed: int = 3) -> Bars:
    return synth_path(seed, [Seg(2 * D, -1.0, 10, 0.1), Seg(30, 3, 10, 0.1), Seg(D - 30, -2.0, 10, 0.1)])


def conflict_day(seed: int = 11) -> Bars:
    return synth_path(seed, [Seg(2 * D, 1.5, 10, 0.1), Seg(40, 0.5, 10, 0.1), Seg(60, -1.0, 10, 0.1), Seg(D - 100, 1.8, 10, 0.1)])


def reversal_day(seed: int = 4) -> Bars:
    return synth_path(seed, [Seg(2 * D, -1.2, 10, 0.1), Seg(20, 0.0, 10, 0.1), Seg(D - 20, 2.0, 10, 0.1)])


def chop_day(seed: int = 3) -> Bars:
    return synth_path(seed, [Seg(3 * D, 0.0, 10, 0.3)])


def random_walk_day(seed: int) -> Bars:
    return synth_path(seed, [Seg(3 * D, 0.0, 10, 0.0)])


class Run:
    def __init__(self, bars: Bars, rp: RegimeParams = RegimeParams(), bp: RibbonParams = RibbonParams()):
        self.bars = bars
        self.rf = vwap_regime(bars, rp)
        self.rb = ribbon(bars, bp)
        self.perp = run_perp(bars, self.rf, self.rb, PerpParams())
        self.inv = run_inventory(bars, self.rf, self.rb, InventoryParams())
        self.s = last_session(bars)
        self.x = bars.minute[self.s] / 60.0

    def cells(self) -> list[str]:
        s = self.s
        return [cell(int(a), int(b) if r else 0) for a, b, r in zip(self.rf.regime[s], self.rb.state[s], self.rb.ready[s])]


# --------------------------------------------------------------------------- #
# Drawing helpers
# --------------------------------------------------------------------------- #


def runs(values):
    """Yield (start, stop, value) for contiguous runs."""
    values = list(values)
    if not values:
        return
    a = 0
    for i in range(1, len(values) + 1):
        if i == len(values) or values[i] != values[a]:
            yield a, i, values[a]
            a = i


def shade_regime(ax, x, regime, alpha=0.75):
    dx = x[1] - x[0]
    for a, b, v in runs(regime):
        col = ABOVE if v > 0 else BELOW if v < 0 else UNDEF
        ax.axvspan(x[a], x[b - 1] + dx, color=col, alpha=alpha, lw=0, zorder=0)


def draw_price(ax, bars: Bars, s: slice, x):
    ax.vlines(x, bars.l[s], bars.h[s], color="#b3b6b7", lw=0.6, zorder=1)
    ax.plot(x, bars.c[s], color=PRICE, lw=0.9, zorder=3, label="close")


def draw_vwap(ax, run: Run, x, band=True):
    s = run.s
    vw = run.rf.vwap_prev[s]
    ax.plot(x, vw, color=VWAP, lw=1.6, zorder=4, label="session VWAP (frozen t-1)")
    if band:
        ax.fill_between(x, vw - run.rf.band[s], vw + run.rf.band[s], color=VWAP, alpha=0.12, lw=0, zorder=2, label="dead band")


def draw_ribbon(ax, run: Run, x, fill=True, lw=1.1):
    s, rb = run.s, run.rb
    ax.plot(x, rb.e_fast[s], color=E21, lw=lw, zorder=4, label="EMA 21")
    ax.plot(x, rb.e_mid[s], color=E50, lw=lw, zorder=4, label="EMA 50")
    ax.plot(x, rb.e_slow[s], color=E100, lw=lw, zorder=4, label="EMA 100")
    if fill:
        for a, b, v in runs(rb.state[s]):
            sl = slice(a, min(b + 1, len(x)))
            ax.fill_between(x[sl], rb.e_fast[s][sl], rb.e_slow[s][sl], color=RIB[v], alpha=0.35, lw=0, zorder=2)


def cut_ribbon(rb: RibbonFrame, s: slice) -> RibbonFrame:
    return RibbonFrame(*(getattr(rb, f)[s] if isinstance(getattr(rb, f), np.ndarray) else getattr(rb, f) for f in RibbonFrame.__dataclass_fields__))


def strip(ax, x, values, colors: dict, label: str):
    dx = x[1] - x[0]
    for a, b, v in runs(values):
        ax.add_patch(Rectangle((x[a], 0), x[b - 1] + dx - x[a], 1, color=colors[v], lw=0))
    ax.set_xlim(x[0], x[-1] + dx)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_ylabel(label, rotation=0, ha="right", va="center", fontsize=8.5)
    ax.grid(False)
    for sp in ("left", "top", "right"):
        ax.spines[sp].set_visible(False)


def regime_strip(ax, run: Run, x):
    strip(ax, run.x, list(run.rf.regime[run.s]), {1: "#58d68d", -1: "#ec7063", 0: UNDEF}, "VWAP side")


def ribbon_strip(ax, run: Run, x):
    st = [int(v) if r else 0 for v, r in zip(run.rb.state[run.s], run.rb.ready[run.s])]
    strip(ax, x, st, RIB, "ribbon")


def cell_strip(ax, run: Run, x):
    strip(ax, x, run.cells(), CELL, "cell")


def mark_perp(ax, run: Run, x, label_reasons=True):
    s0 = run.s.start
    xs = lambda t: x[t - s0]  # noqa: E731
    for f in run.perp.fills:
        if f.t < s0:
            continue
        r = f.reason
        if r.startswith("ENTRY"):
            up = f.units > 0
            ax.scatter(xs(f.t), f.px, marker="^" if up else "v", s=110, color=LONG if up else SHORT, edgecolor="k", lw=0.6, zorder=7)
            ax.annotate("ENTRY " + ("LONG" if up else "SHORT"), (xs(f.t), f.px), xytext=(6, -16 if up else 10), textcoords="offset points", fontsize=8, weight="bold")
        elif r == "ADD":
            ax.scatter(xs(f.t), f.px, marker="P", s=80, color="#2471a3", edgecolor="k", lw=0.5, zorder=7)
            if label_reasons:
                ax.annotate("ADD +0.5", (xs(f.t), f.px), xytext=(6, -14), textcoords="offset points", fontsize=8)
        elif r.startswith("REDUCE"):
            ax.scatter(xs(f.t), f.px, marker="D", s=46, color="#f1c40f", edgecolor="k", lw=0.5, zorder=7)
            if label_reasons:
                ax.annotate(r.replace("REDUCE_", "REDUCE "), (xs(f.t), f.px), xytext=(6, 8), textcoords="offset points", fontsize=7.5)
        else:
            ax.scatter(xs(f.t), f.px, marker="X", s=70, color="k", zorder=7)
            if label_reasons:
                ax.annotate(r, (xs(f.t), f.px), xytext=(-10, 10), textcoords="offset points", fontsize=7.5, ha="right")
    for ep in run.perp.episodes:
        if ep.entry_t < s0:
            continue
        end = ep.exit_t if ep.exit_t is not None else run.s.stop - 1
        col = SHORT if ep.side > 0 else LONG
        moved = ep.add_t if ep.add_t is not None else end
        ax.hlines(ep.initial_stop_px, xs(ep.entry_t), xs(moved), color=col, lw=1.0, ls=":", zorder=5)
        if ep.add_t is not None:
            ax.hlines(ep.stop_px, xs(ep.add_t), xs(end), color=col, lw=1.0, ls="--", alpha=0.7, zorder=5)
            ax.vlines(xs(ep.add_t), ep.initial_stop_px, ep.stop_px, color=col, lw=0.6, ls=":", zorder=5)


def session_equity(run: Run, eq: np.ndarray) -> np.ndarray:
    s = run.s
    base = eq[s.start - 1] if s.start > 0 else 0.0
    return eq[s] - base


def hour_axis(ax):
    ax.set_xlabel("hours since session anchor (00:00 UTC)")
    ax.set_xticks(range(0, 25, 3))


# --------------------------------------------------------------------------- #
# fig01: two regimes
# --------------------------------------------------------------------------- #


def fig01():
    run = Run(reversal_day(2))
    b, s, x, rf = run.bars, run.s, run.x, run.rf
    fig = plt.figure(figsize=(12.5, 6.6))
    gs = fig.add_gridspec(2, 1, height_ratios=[5, 0.5], hspace=0.08)
    ax = fig.add_subplot(gs[0])
    shade_regime(ax, x, rf.regime[s])
    draw_price(ax, b, s, x)
    draw_vwap(ax, run, x)
    c = b.c[s]
    vw = rf.vwap_prev[s]
    raw = np.flatnonzero(np.isfinite(vw[1:]) & np.isfinite(vw[:-1]) & (np.sign(c[1:] - vw[1:]) != np.sign(c[:-1] - vw[:-1]))) + 1
    lo = np.nanmin(b.l[s])
    ax.scatter(x[raw], np.full(len(raw), lo), marker="|", s=90, color="#7f8c8d", zorder=5, label=f"raw close-vs-VWAP crosses ({len(raw)})")
    cracks = np.flatnonzero(rf.crack[s])
    lo_px, hi_px = np.nanmin(b.l[s]), np.nanmax(b.h[s])
    ax.set_ylim(lo_px - 0.12 * (hi_px - lo_px), hi_px + 0.03 * (hi_px - lo_px))
    offsets = [(-10, 70), (30, -32), (60, 40), (40, -40)]
    for k, t in enumerate(cracks):
        up = rf.crack[s][t] > 0
        ax.scatter(x[t], c[t], s=150, marker="o", facecolor="none", edgecolor=LONG if up else SHORT, lw=2.0, zorder=6)
        word = "ESTABLISHED" if k == 0 else "CRACK"
        ax.annotate(
            f"{word}: -> {'ABOVE' if up else 'BELOW'}",
            (x[t], c[t]),
            xytext=offsets[k % len(offsets)],
            textcoords="offset points",
            fontsize=8.5,
            weight="bold",
            color=LONG if up else SHORT,
            arrowprops=dict(arrowstyle="->", lw=0.8, color=LONG if up else SHORT),
        )
    ax.text(
        0.99,
        0.03,
        "A regime is established or cracked only after 2 consecutive closes\n"
        "beyond the dead band (max(0.25 sigma, 5 bps) around VWAP frozen at t-1).\n"
        "Closes inside the band never change the regime.",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.5,
        bbox=dict(fc="white", ec="#aaa"),
    )
    ax.axvline(1.0, color="#7f8c8d", lw=0.8, ls="--")
    ax.text(0.05, 0.97, "warm-up:\nUNDEFINED\n(no regime)", transform=ax.get_xaxis_transform(), va="top", fontsize=8, color="#555")
    ax.set_title(f"Fig01. Two regimes around the session VWAP: {len(raw)} raw crosses, {len(cracks)} confirmed regime changes")
    ax.set_ylabel("price (synthetic index)")
    hs = ax.get_legend_handles_labels()
    hs[0].extend([Patch(color=ABOVE, label="ABOVE regime (bullish)"), Patch(color=BELOW, label="BELOW regime (bearish)")])
    ax.legend(handles=hs[0], loc="upper left", bbox_to_anchor=(0.09, 1.0), ncol=2)
    ax.set_xlim(x[0], x[-1] + 1 / 12)
    ax.tick_params(labelbottom=False)
    a2 = fig.add_subplot(gs[1], sharex=ax)
    regime_strip(a2, run, x)
    hour_axis(a2)
    tag(fig)
    fig.savefig(OUT / "fig01_two_regimes.png", bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# fig02: ribbon intact vs tangled
# --------------------------------------------------------------------------- #


def fig02():
    tr = Run(bull_day(5))
    ch = Run(chop_day(3))
    fig = plt.figure(figsize=(13.5, 7.2))
    gs = fig.add_gridspec(3, 2, height_ratios=[5, 0.45, 1.6], hspace=0.12, wspace=0.12, top=0.9)
    for col, (run, title) in enumerate([(tr, "INTACT: ordered, sloped, separated, persistent"), (ch, "TANGLED: braided, flat, crossing")]):
        b, s, x, rb = run.bars, run.s, run.x, run.rb
        ax = fig.add_subplot(gs[0, col])
        draw_price(ax, b, s, x)
        draw_ribbon(ax, run, x)
        ax.set_title(("Left. " if col == 0 else "Right. ") + title, fontsize=10)
        ax.set_xlim(x[0], x[-1] + 1 / 12)
        ax.tick_params(labelbottom=False)
        if col == 0:
            ax.set_ylabel("price (synthetic index)")
            ax.legend(loc="upper left", ncol=4)
            i = int(np.argmax(x >= 15.0))
            t = s.start + i
            ef, em, es = rb.e_fast[t], rb.e_mid[t], rb.e_slow[t]
            for y0, y1, lab in [(em, ef, "gap 21-50"), (es, em, "gap 50-100")]:
                ax.annotate("", (x[i], y1), (x[i], y0), arrowprops=dict(arrowstyle="<->", lw=1.0))
            ax.text(x[i] + 0.25, (ef + es) / 2, f"min gap = {rb.gap_atr[t]:.2f} ATR\n(needs >= 0.15 to qualify,\n>= 0.05 to stay intact)", fontsize=8, va="center")
        else:
            fm = np.sign(rb.e_fast[s] - rb.e_mid[s])
            xi = np.flatnonzero(fm[1:] != fm[:-1]) + 1
            ax.scatter(x[xi], rb.e_mid[s][xi], marker="x", s=36, color="k", zorder=6, label=f"EMA21/EMA50 crosses ({len(xi)})")
            ax.legend(loc="upper left")
        a2 = fig.add_subplot(gs[1, col], sharex=ax)
        ribbon_strip(a2, run, x)
        a2.tick_params(labelbottom=False)
        a3 = fig.add_subplot(gs[2, col], sharex=ax)
        a3.plot(x, rb.gap_atr[s] * rb.order[s], color="#34495e", lw=1.0, label="signed min gap (ATR; 0 when not ordered)")
        a3.axhline(0.15, color=LONG, lw=0.8, ls="--")
        a3.axhline(-0.15, color=SHORT, lw=0.8, ls="--")
        a3.plot(x, rb.fast_crosses[s] / 5.0, color="#7f8c8d", lw=0.9, ls="-.", label="EMA21/50 crosses in last 4h (/5)")
        a3.set_ylim(-2.2, 2.2)
        a3.legend(loc="lower left", fontsize=7.5, ncol=2)
        hour_axis(a3)
    h = [Patch(color=RIB[k], label=n) for k, n in [(2, "BULL_INTACT"), (1, "BULL_WEAK"), (0, "TANGLED"), (-1, "BEAR_WEAK"), (-2, "BEAR_INTACT")]]
    fig.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=5, fontsize=8.5)
    fig.suptitle("Fig02. EMA 21/50/100 ribbon: what 'intact' means operationally", fontweight="bold", y=0.995)
    tag(fig)
    fig.savefig(OUT / "fig02_ribbon_intact_vs_tangled.png", bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# fig03 / fig04: annotated perp trades
# --------------------------------------------------------------------------- #


def trade_figure(run: Run, title: str, fname: str, note: str):
    b, s, x = run.bars, run.s, run.x
    fig = plt.figure(figsize=(13, 8.4))
    gs = fig.add_gridspec(5, 1, height_ratios=[5, 0.4, 0.4, 0.4, 1.7], hspace=0.1)
    ax = fig.add_subplot(gs[0])
    shade_regime(ax, x, run.rf.regime[s], alpha=0.55)
    draw_price(ax, b, s, x)
    draw_vwap(ax, run, x)
    draw_ribbon(ax, run, x)
    mark_perp(ax, run, x)
    ax.set_xlim(x[0], x[-1] + 1 / 12)
    ax.set_ylabel("price (synthetic index)")
    ax.set_title(title)
    ax.legend(loc="upper left", ncol=3)
    ax.text(0.99, 0.02, note, transform=ax.transAxes, ha="right", va="bottom", fontsize=8, bbox=dict(fc="white", ec="#aaa", alpha=0.9))
    ax.tick_params(labelbottom=False)
    for i, fn in enumerate((regime_strip, ribbon_strip, cell_strip)):
        a = fig.add_subplot(gs[1 + i], sharex=ax)
        fn(a, run, x)
        a.tick_params(labelbottom=False)
    a = fig.add_subplot(gs[4], sharex=ax)
    a.step(x, run.perp.position[s], where="post", color="#2c3e50", lw=1.2, label="Book B position (units)")
    a.set_ylabel("units")
    a.set_ylim(-1.8, 1.8)
    a2 = a.twinx()
    a2.plot(x, session_equity(run, run.perp.equity_bps), color="#2471a3", lw=1.2, label="Book B net P&L (bps)")
    a2.set_ylabel("bps")
    a2.grid(False)
    h1, l1 = a.get_legend_handles_labels()
    h2, l2 = a2.get_legend_handles_labels()
    a.legend(h1 + h2, l1 + l2, loc="upper left", ncol=2)
    hour_axis(a)
    tag(fig)
    fig.savefig(OUT / fname, bbox_inches="tight")
    plt.close(fig)


def episode_note(run: Run) -> str:
    lines = []
    for ep in run.perp.episodes:
        if ep.entry_t < run.s.start:
            continue
        side = "LONG" if ep.side > 0 else "SHORT"
        lines.append(f"{side} {ep.exit_reason}: {ep.pnl_bps:+.0f} bps net ({ep.r_multiple:+.1f}R, R={ep.r_bps:.0f} bps)")
    return "\n".join(lines) if lines else "no Book B trades"


def fig03():
    run = Run(bull_day(5))
    trade_figure(
        run,
        "Fig03. Long above VWAP with a bullish ribbon: Book B enters only when both agree",
        "fig03_long_above_vwap_bull_ribbon.png",
        episode_note(run) + STOP_NOTE,
    )


STOP_NOTE = "\ndotted = initial hard stop (beyond far edge of VWAP band, >= 2 ATR); dashed = stop moved to entry after the add"


def fig04():
    run = Run(bear_day(3))
    trade_figure(
        run,
        "Fig04. Short below VWAP with a bearish ribbon: mirror rules",
        "fig04_short_below_vwap_bear_ribbon.png",
        episode_note(run) + STOP_NOTE,
    )


# --------------------------------------------------------------------------- #
# fig05: conflict
# --------------------------------------------------------------------------- #


def fig05():
    run = Run(conflict_day(11))
    b, s, x = run.bars, run.s, run.x
    bs = b.slice(s.start)
    naive_rf = vwap_regime(bs, RegimeParams())
    npos, neq, nch = run_side_follow(bs, naive_rf)
    cells = run.cells()
    fig = plt.figure(figsize=(13, 8.6))
    gs = fig.add_gridspec(5, 1, height_ratios=[5, 0.4, 0.4, 0.4, 2.0], hspace=0.1)
    ax = fig.add_subplot(gs[0])
    shade_regime(ax, x, run.rf.regime[s], alpha=0.45)
    dx = x[1] - x[0]
    for a, bb, v in runs(cells):
        if v == "CONFLICT":
            ax.axvspan(x[a], x[bb - 1] + dx, facecolor="none", edgecolor=CELL["CONFLICT"], hatch="///", lw=0, alpha=0.6, zorder=1)
    draw_price(ax, b, s, x)
    draw_vwap(ax, run, x)
    draw_ribbon(ax, run, x)
    mark_perp(ax, run, x, label_reasons=False)
    ax.text(0.99, 0.03, "Book B episodes:\n" + episode_note(run), transform=ax.transAxes, ha="right", va="bottom", fontsize=8, bbox=dict(fc="white", ec="#aaa", alpha=0.9))
    flips = np.flatnonzero(np.diff(npos) != 0) + 1
    ax.scatter(x[flips], b.o[s][flips], marker="o", s=18, color="#7f8c8d", zorder=6, label="naive VWAP-side position changes")
    ci = [i for i, k in enumerate(cells) if k == "CONFLICT"]
    if ci:
        i = ci[len(ci) // 2]
        ax.annotate(
            "CONFLICT: below VWAP but ribbon still BULL\nBook B: no short (and no long)\nBook A: inventory target 0 (neutral quoting)",
            (x[i], b.c[s][i]),
            xytext=(30, -70),
            textcoords="offset points",
            fontsize=8.5,
            bbox=dict(fc="white", ec=CELL["CONFLICT"]),
            arrowprops=dict(arrowstyle="->", color=CELL["CONFLICT"]),
        )
    ax.set_xlim(x[0], x[-1] + dx)
    ax.set_ylabel("price (synthetic index)")
    ax.set_title("Fig05. Conflict case: below VWAP while the ribbon is still bullish -> do not trade the VWAP side")
    h, _ = ax.get_legend_handles_labels()
    h += [Patch(facecolor="none", edgecolor=CELL["CONFLICT"], hatch="///", label="CONFLICT cell")]
    ax.legend(handles=h, loc="upper left", ncol=3)
    ax.tick_params(labelbottom=False)
    for i, fn in enumerate((regime_strip, ribbon_strip, cell_strip)):
        a = fig.add_subplot(gs[1 + i], sharex=ax)
        fn(a, run, x)
        a.tick_params(labelbottom=False)
    a = fig.add_subplot(gs[4], sharex=ax)
    a.plot(x, neq, color="#7f8c8d", lw=1.2, label=f"naive VWAP-side (no ribbon gate): {neq[-1]:+.0f} bps, {nch} position changes")
    a.plot(x, session_equity(run, run.perp.equity_bps), color="#2471a3", lw=1.4, label=f"Book B (ribbon-gated): {session_equity(run, run.perp.equity_bps)[-1]:+.0f} bps")
    a.plot(x, session_equity(run, run.inv.equity_bps), color="#16a085", lw=1.2, ls="--", label=f"Book A (inventory skew): {session_equity(run, run.inv.equity_bps)[-1]:+.0f} bps")
    a.axhline(0, color="k", lw=0.6)
    a.set_ylabel("net bps")
    a.legend(loc="upper left", fontsize=8)
    hour_axis(a)
    tag(fig)
    fig.savefig(OUT / "fig05_conflict_no_trade.png", bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# fig06: decision matrix
# --------------------------------------------------------------------------- #


def fig06():
    ip = InventoryParams()
    cols = [(-2, "BEAR_INTACT"), (-1, "BEAR_WEAK"), (0, "TANGLED"), (1, "BULL_WEAK"), (2, "BULL_INTACT")]
    rows = [(1, "ABOVE VWAP\n(bullish regime)"), (-1, "BELOW VWAP\n(bearish regime)"), (0, "UNDEFINED\n(warm-up / no\nconfirmed side)")]
    mult = {"AGREE": ip.mult_agree, "WEAK": ip.mult_weak, "TANGLED": ip.mult_tangled, "CONFLICT": ip.mult_conflict, "UNDEFINED": 0.0}
    perp = {"AGREE": "ENTER / HOLD\n(add at +1R)", "WEAK": "no entry;\nREDUCE if held", "TANGLED": "FLAT\n(ribbon break kill)", "CONFLICT": "FLAT\n(do not trade)", "UNDEFINED": "FLAT"}
    fig, ax = plt.subplots(figsize=(13, 5.6))
    for i, (reg, rname) in enumerate(rows):
        for j, (st, _) in enumerate(cols):
            k = cell(reg, st)
            ax.add_patch(Rectangle((j, -i), 1, 1, fc=CELL[k], ec="white", lw=3, alpha=0.85))
            q = reg * ip.lean * mult[k]
            side = "" if reg == 0 else ("long" if reg > 0 else "short")
            inv = "q* = 0 (neutral)" if q == 0 else f"q* = {q:+.1f} q_max ({side})"
            ax.text(j + 0.5, -i + 0.80, k, ha="center", va="center", fontsize=9.5, weight="bold")
            ax.text(j + 0.5, -i + 0.52, "A: " + inv, ha="center", va="center", fontsize=8.5)
            bdir = "" if k != "AGREE" else (" LONG" if reg > 0 else " SHORT")
            ax.text(j + 0.5, -i + 0.24, "B: " + perp[k].replace("ENTER", "ENTER" + bdir), ha="center", va="center", fontsize=8.2)
    ax.set_xlim(0, 5)
    ax.set_ylim(-2, 1)
    ax.set_xticks([j + 0.5 for j in range(5)])
    ax.set_xticklabels([n for _, n in cols])
    ax.xaxis.tick_top()
    ax.set_yticks([-i + 0.5 for i in range(3)])
    ax.set_yticklabels([n for _, n in rows])
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title("Fig06. Decision matrix: VWAP side x ribbon state -> Book A inventory target and Book B action", pad=28)
    fig.text(
        0.5,
        0.035,
        "A = inventory-skew paper book (target q*, lean = 0.6 q_max). B = perp directional paper book. "
        "Kill switches (session flat, event blackout, loss limits) override every cell.",
        ha="center",
        fontsize=8.5,
    )
    tag(fig, "RULE ILLUSTRATION (paper rule contract v0 defaults; placeholders, not tuned)")
    fig.savefig(OUT / "fig06_decision_matrix.png", bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# fig07: inventory book
# --------------------------------------------------------------------------- #


def fig07():
    run = Run(reversal_day(4))
    b, s, x = run.bars, run.s, run.x
    ir = run.inv
    neutral = run_inventory(b, run.rf, run.rb, InventoryParams(lean=0.0))
    fig = plt.figure(figsize=(14, 8.4))
    gs = fig.add_gridspec(3, 2, width_ratios=[3, 1.25], height_ratios=[4, 0.4, 2.2], hspace=0.1, wspace=0.18)
    ax = fig.add_subplot(gs[0, 0])
    shade_regime(ax, x, run.rf.regime[s], alpha=0.5)
    draw_price(ax, b, s, x)
    draw_vwap(ax, run, x, band=False)
    draw_ribbon(ax, run, x, fill=False, lw=0.8)
    s0 = s.start
    buys = [f for f in ir.fills if f.t >= s0 and f.qty > 0 and f.maker]
    sells = [f for f in ir.fills if f.t >= s0 and f.qty < 0 and f.maker]
    ax.scatter([x[f.t - s0] for f in buys], [f.px for f in buys], marker="^", s=12, color=LONG, alpha=0.7, zorder=6, label=f"passive buys ({len(buys)})")
    ax.scatter([x[f.t - s0] for f in sells], [f.px for f in sells], marker="v", s=12, color=SHORT, alpha=0.7, zorder=6, label=f"passive sells ({len(sells)})")
    ax.set_title("Fig07a. Book A, reversal day: neutral while tangled, lean long once side and ribbon agree", fontsize=10)
    ax.set_ylabel("price (synthetic index)")
    ax.legend(loc="upper left", ncol=3)
    ax.set_xlim(x[0], x[-1] + 1 / 12)
    ax.tick_params(labelbottom=False)
    a1 = fig.add_subplot(gs[1, 0], sharex=ax)
    cell_strip(a1, run, x)
    a1.tick_params(labelbottom=False)
    a2 = fig.add_subplot(gs[2, 0], sharex=ax)
    a2.step(x, ir.q_target[s], where="post", color="#7f8c8d", lw=1.2, ls="--", label="target q*")
    a2.plot(x, ir.q[s], color="#16a085", lw=1.4, label="paper inventory q")
    a2.plot(x, neutral.q[s], color="#d35400", lw=0.9, alpha=0.8, label="neutral MM inventory (no lean)")
    a2.axhline(0, color="k", lw=0.6)
    a2.set_ylabel("inventory (x q_max)")
    a2.set_ylim(-1.05, 1.05)
    a2.legend(loc="upper left", ncol=3, fontsize=8)
    a2.text(
        0.99,
        0.04,
        f"session net: lean book {session_equity(run, ir.equity_bps)[-1]:+.0f} bps, neutral MM {session_equity(run, neutral.equity_bps)[-1]:+.0f} bps (of q_max notional)",
        transform=a2.transAxes,
        fontsize=8,
        ha="right",
    )
    hour_axis(a2)

    hz = (1, 3, 6, 12)
    acc = {"with": [], "against": [], "neutral": []}
    for sd in range(1, 31):
        for mk in (reversal_day, bull_day, bear_day, conflict_day, chop_day):
            rr = Run(mk(sd))
            m = markouts(rr.bars, [f for f in rr.inv.fills if f.t >= rr.s.start])
            if len(m["side"]) == 0:
                continue
            neutral_mask = np.array([f.q_target == 0 for f in rr.inv.fills if f.t >= rr.s.start and f.maker])
            acc["with"].append(m["markout"][m["with_lean"]])
            acc["against"].append(m["markout"][~m["with_lean"] & ~neutral_mask])
            acc["neutral"].append(m["markout"][neutral_mask])
    a3 = fig.add_subplot(gs[:, 1])
    w = 0.26
    for i, (k, col, lab) in enumerate([("with", "#16a085", "fills WITH the lean"), ("against", "#c0392b", "fills AGAINST the lean"), ("neutral", "#7f8c8d", "fills while q* = 0")]):
        arr = np.vstack(acc[k]) if acc[k] else np.zeros((0, len(hz)))
        mu = np.nanmean(arr, axis=0)
        print(f"  fig07 markout {k:8s} n={len(arr)} " + " ".join(f"{v:+.1f}" for v in mu))
        a3.bar(np.arange(len(hz)) + (i - 1) * w, mu, width=w, color=col, label=f"{lab} (n={len(arr)})")
    a3.axhline(0, color="k", lw=0.6)
    a3.set_xticks(range(len(hz)))
    a3.set_xticklabels([f"+{h * 5}m" for h in hz])
    a3.set_ylabel("mean markout per fill (bps, + = good)")
    a3.set_title("Fig07b. Markouts by lean alignment\n(150 seeded sessions, 5 scenario types)", fontsize=10)
    a3.legend(loc="lower left", fontsize=7.5)
    tag(fig, TAG + "; bar-based fill model (trade-through), no queue position: markouts here are mechanical, not evidence")
    fig.savefig(OUT / "fig07_inventory_book.png", bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# fig08: whipsaw and the null
# --------------------------------------------------------------------------- #


def fig08():
    families = [("trend days", lambda sd: bull_day(sd) if sd % 2 else bear_day(sd)), ("chop (mean-reverting)", chop_day), ("random walk (null)", random_walk_day)]
    variants = [
        ("naive: raw close vs VWAP", RegimeParams(dead_band_sigma=0.0, dead_band_floor_bps=0.0, accept_bars=1), False),
        ("dead band + 2-close acceptance", RegimeParams(), False),
        ("band + acceptance + ribbon gate", RegimeParams(), True),
    ]
    cols = ["#95a5a6", "#5dade2", "#1f5fbf"]
    res = {}
    for fname, mk in families:
        for vname, rp, gate in variants:
            pnl, flips = [], []
            for sd in range(1, 41):
                b = mk(sd)
                s = last_session(b)
                bs = b.slice(s.start)
                rb = cut_ribbon(ribbon(b), s) if gate else None
                _, eq, ch = run_side_follow(bs, vwap_regime(bs, rp), rb)
                pnl.append(eq[-1])
                flips.append(ch)
            res[(fname, vname)] = (np.array(pnl), np.array(flips))
            print(f"  fig08 {fname:24s} {vname:34s} pnl {np.mean(pnl):+8.1f} bps  changes {np.mean(flips):5.1f}")
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4))
    w = 0.26
    floor = -450.0
    for j, (vname, _, _) in enumerate(variants):
        mu = np.array([res[(f, vname)][0].mean() for f, _ in families])
        se = np.array([res[(f, vname)][0].std(ddof=1) / np.sqrt(len(res[(f, vname)][0])) for f, _ in families])
        xs = np.arange(3) + (j - 1) * w
        axes[0].bar(xs, np.maximum(mu, floor), width=w, yerr=np.where(mu > floor, se, 0), color=cols[j], label=vname, capsize=3)
        for xi, m in zip(xs, mu):
            if m < floor:
                axes[0].text(xi, floor + 12, f"{m:+.0f}\n(clipped)", ha="center", va="bottom", fontsize=7.2, color="white", weight="bold")
            else:
                axes[0].text(xi, m + (6 if m >= 0 else -6), f"{m:+.0f}", ha="center", va="bottom" if m >= 0 else "top", fontsize=7.5)
        fl = [res[(f, vname)][1].mean() for f, _ in families]
        axes[1].bar(xs, fl, width=w, color=cols[j], label=vname)
    for a in axes:
        a.set_xticks(range(3))
        a.set_xticklabels([f for f, _ in families])
        a.axhline(0, color="k", lw=0.6)
    axes[0].set_ylabel("mean net bps per session (6 bps per unit change), +/- 1 s.e.")
    axes[0].set_ylim(floor - 130, 380)
    axes[0].set_title("Fig08a. Net P&L of 'hold the VWAP side' (40 sessions each)", fontsize=10)
    axes[1].set_ylabel("position changes per session")
    axes[1].set_title("Fig08b. Whipsaw: how often each variant changes position", fontsize=10)
    axes[0].legend(loc="upper right", fontsize=8)
    fig.suptitle("Fig08. The dead band and acceptance rule cut whipsaw; the ribbon gate cuts chop losses; nothing beats a random walk", fontweight="bold")
    tag(fig, TAG + "; trend/chop generators were chosen to show the mechanism, so the trend-day result is circular")
    fig.savefig(OUT / "fig08_whipsaw_and_null.png", bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# fig09: lag between the VWAP crack and the ribbon
# --------------------------------------------------------------------------- #


def fig09():
    run = Run(reversal_day(4))
    b, s, x, rf, rb = run.bars, run.s, run.x, run.rf, run.rb
    fig = plt.figure(figsize=(14, 6.4))
    gs = fig.add_gridspec(3, 2, width_ratios=[2.6, 1], height_ratios=[4, 0.4, 0.4], hspace=0.1, wspace=0.18)
    ax = fig.add_subplot(gs[0, 0])
    shade_regime(ax, x, rf.regime[s], alpha=0.5)
    draw_price(ax, b, s, x)
    draw_vwap(ax, run, x)
    draw_ribbon(ax, run, x)
    up = [i for i in np.flatnonzero(rf.crack[s] > 0)]
    intact = np.flatnonzero(rb.state[s] == 2)
    if up and len(intact):
        i0 = up[0]
        later = intact[intact >= i0]
        if len(later):
            i1 = int(later[0])
            lo_px, hi_px = np.nanmin(b.l[s]), np.nanmax(b.h[s])
            ymax = lo_px + 0.62 * (hi_px - lo_px)
            ax.annotate("", (x[i1], ymax), (x[i0], ymax), arrowprops=dict(arrowstyle="<->", lw=1.3, color="#d35400"))
            ax.text((x[i0] + x[i1]) / 2, ymax, f"lag {(i1 - i0) * 5 / 60:.1f} h: VWAP says long,\nribbon not yet intact", ha="center", va="bottom", fontsize=8.5, color="#d35400")
            ax.axvline(x[i0], color=LONG, lw=0.9, ls="--")
            ax.axvline(x[i1], color="#27ae60", lw=0.9, ls=":")
    mark_perp(ax, run, x, label_reasons=False)
    ax.set_title("Fig09a. EMA lag: the VWAP crack comes first, ribbon confirmation comes later")
    ax.set_ylabel("price (synthetic index)")
    ax.legend(loc="lower right", ncol=3)
    ax.set_xlim(x[0], x[-1] + 1 / 12)
    ax.tick_params(labelbottom=False)
    a1 = fig.add_subplot(gs[1, 0], sharex=ax)
    regime_strip(a1, run, x)
    a1.tick_params(labelbottom=False)
    a2 = fig.add_subplot(gs[2, 0], sharex=ax)
    ribbon_strip(a2, run, x)
    hour_axis(a2)

    lags, never = [], 0
    for sd in range(1, 81):
        rr = Run(reversal_day(sd))
        st, cr = rr.rb.state[rr.s], rr.rf.crack[rr.s]
        ups = np.flatnonzero(cr > 0)
        if not len(ups):
            never += 1
            continue
        i0 = ups[0]
        later = np.flatnonzero(st[i0:] == 2)
        if len(later):
            lags.append(later[0] * 5 / 60)
        else:
            never += 1
    a3 = fig.add_subplot(gs[:, 1])
    a3.hist(lags, bins=np.arange(0, 12.5, 0.5), color="#d35400", alpha=0.8)
    a3.set_xlabel("hours from first VWAP crack UP to BULL_INTACT")
    a3.set_ylabel("sessions")
    med = np.median(lags) if lags else float("nan")
    print(f"  fig09 lag median {med:.2f} h, p10 {np.percentile(lags, 10):.2f}, p90 {np.percentile(lags, 90):.2f}, never {never}/80")
    a3.axvline(med, color="k", lw=0.9, ls="--")
    a3.set_title(f"Fig09b. Lag on 80 seeded V-reversal days\nmedian {med:.1f} h; {never} never confirmed in-session", fontsize=10)
    tag(fig)
    fig.savefig(OUT / "fig09_lag_vwap_vs_ribbon.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09):
        f()
        print("wrote", f.__name__)
