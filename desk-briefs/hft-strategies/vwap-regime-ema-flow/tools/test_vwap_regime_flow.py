"""Causality and rule-invariant checks for the VWAP regime + EMA ribbon engine.

    python3 desk-briefs/hft-strategies/vwap-regime-ema-flow/tools/test_vwap_regime_flow.py
    # or: pytest desk-briefs/hft-strategies/vwap-regime-ema-flow/tools
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vwap_regime_flow import (  # noqa: E402
    SESSION_BARS,
    Bars,
    InventoryParams,
    PerpParams,
    RegimeParams,
    RibbonParams,
    Seg,
    ema,
    ribbon,
    run_inventory,
    run_perp,
    synth_path,
    vwap_regime,
)

D = SESSION_BARS


def _trend_path(seed: int = 3) -> Bars:
    return synth_path(seed, [Seg(2 * D, 1.0, 10, 0.1), Seg(30, -3, 10, 0.1), Seg(D - 30, 2.0, 10, 0.1)])


def _chop_path(seed: int = 4) -> Bars:
    return synth_path(seed, [Seg(3 * D, 0.0, 10, 0.3)])


def _perturb_after(b: Bars, k: int, seed: int = 99) -> Bars:
    rng = np.random.default_rng(seed)
    out = Bars(*(getattr(b, f).copy() for f in ("o", "h", "l", "c", "v", "session", "minute")))
    m = len(b) - k
    scale = np.exp(np.cumsum(rng.normal(0, 0.003, m)))
    for f in ("o", "h", "l", "c"):
        getattr(out, f)[k:] *= scale
    out.h[k:] = np.maximum.reduce([out.o[k:], out.h[k:], out.c[k:]])
    out.l[k:] = np.minimum.reduce([out.o[k:], out.l[k:], out.c[k:]])
    out.v[k:] *= rng.lognormal(0, 1, m)
    return out


def test_frames_are_causal():
    b = _trend_path()
    k = 2 * D + 140
    b2 = _perturb_after(b, k)
    rf0, rf1 = vwap_regime(b), vwap_regime(b2)
    rb0, rb1 = ribbon(b), ribbon(b2)
    np.testing.assert_allclose(rf0.vwap_prev[: k + 1], rf1.vwap_prev[: k + 1], equal_nan=True)
    np.testing.assert_allclose(rf0.sigma_prev[: k + 1], rf1.sigma_prev[: k + 1], equal_nan=True)
    assert np.array_equal(rf0.regime[:k], rf1.regime[:k])
    assert np.array_equal(rb0.state[:k], rb1.state[:k])
    np.testing.assert_allclose(rb0.e_slow[:k], rb1.e_slow[:k])


def test_book_decisions_before_k_unchanged_by_future():
    for b in (_trend_path(), _chop_path()):
        k = 2 * D + 150
        b2 = _perturb_after(b, k)
        p0 = run_perp(b, vwap_regime(b), ribbon(b))
        p1 = run_perp(b2, vwap_regime(b2), ribbon(b2))
        assert [e for e in p0.events if e[0] < k] == [e for e in p1.events if e[0] < k]
        i0 = run_inventory(b, vwap_regime(b), ribbon(b))
        i1 = run_inventory(b2, vwap_regime(b2), ribbon(b2))
        np.testing.assert_allclose(i0.q_target[:k], i1.q_target[:k])
        np.testing.assert_allclose(i0.q[:k], i1.q[:k])


def test_session_vwap_resets_and_warmup_is_undefined():
    b = _trend_path()
    rp = RegimeParams()
    rf = vwap_regime(b, rp)
    starts = np.flatnonzero(np.diff(b.session)) + 1
    assert np.all(np.isnan(rf.vwap_prev[starts]))
    assert np.all(rf.regime[b.minute < rp.warmup_minutes] == 0)


def test_acceptance_needs_consecutive_closes():
    n = 40
    c = np.full(n, 100.0)
    c[20] = 101.0
    c[21] = 100.0
    c[30:32] = 101.0
    minute = np.arange(n) * 5
    b = Bars(c.copy(), c + 0.01, c - 0.01, c.copy(), np.ones(n), np.zeros(n, int), minute)
    rf = vwap_regime(b, RegimeParams(warmup_minutes=10, accept_bars=2))
    assert rf.side_raw[20] == 1 and rf.regime[20] == 0 and rf.regime[21] == 0
    assert rf.regime[30] == 0 and rf.regime[31] == 1 and rf.crack[31] == 1


def test_ema_seed_decays_and_ribbon_waits_for_warmup():
    x = np.linspace(100, 110, 600)
    a, b = ema(x, 100), ema(x[1:], 100)
    alpha = 2.0 / 101.0
    lag = np.arange(1, 600)
    expected = (a[1] - x[1]) * (1 - alpha) ** (lag - 1)
    np.testing.assert_allclose(a[1:] - b, expected, atol=1e-9)
    bars = _trend_path()
    rb = ribbon(bars, RibbonParams())
    assert not rb.ready[: RibbonParams().warmup_bars].any()
    assert np.all(rb.state[: RibbonParams().warmup_bars] == 0)


def test_perp_entries_only_in_agree_cell():
    for b in (_trend_path(1), _trend_path(2), _chop_path(5)):
        rf, rb = vwap_regime(b), ribbon(b)
        pr = run_perp(b, rf, rb)
        for e in pr.episodes:
            s = e.signal_t
            assert rf.regime[s] == e.side
            assert rb.state[s] == 2 * e.side
            assert rf.side_raw[s] == e.side


def test_perp_kills_fire_next_bar():
    for b in (_trend_path(1), _trend_path(2), _chop_path(5)):
        rf, rb = vwap_regime(b), ribbon(b)
        pr = run_perp(b, rf, rb)
        pos = pr.position
        for t in range(len(b) - 1):
            s = np.sign(pos[t])
            if s != 0 and (rf.regime[t] == -s or rb.state[t] * s <= 0):
                assert pos[t + 1] == 0, t


def test_flat_into_session_end_and_inventory_bounded():
    for b in (_trend_path(1), _chop_path(5)):
        rf, rb = vwap_regime(b), ribbon(b)
        pr = run_perp(b, rf, rb, PerpParams())
        ip = InventoryParams()
        ir = run_inventory(b, rf, rb, ip)
        last = np.flatnonzero(np.diff(b.session) != 0)
        last = np.append(last, len(b) - 1)
        assert np.all(pr.position[last] == 0)
        assert np.all(np.abs(ir.q[last]) < 1e-9)
        assert np.all(np.abs(ir.q) <= ip.q_max + 1e-9)
        assert np.all(ir.q_target[rf.regime == 0] == 0)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
