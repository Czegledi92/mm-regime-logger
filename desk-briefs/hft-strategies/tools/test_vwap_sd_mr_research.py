"""Causality and semantics checks for the research engines.

    python3 desk-briefs/hft-strategies/tools/test_vwap_sd_mr_research.py
    # or: pytest desk-briefs/hft-strategies/tools
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vwap_sd_mr_research import Bars, Shock, V1Params, run_v1, run_vault, synth_multiday, synth_session  # noqa: E402


def _perturb_after(b: Bars, k: int, seed: int = 99) -> Bars:
    rng = np.random.default_rng(seed)
    out = Bars(*(getattr(b, f).copy() for f in ("o", "h", "l", "c", "v", "session", "minute")))
    bump = rng.normal(0, 0.5, len(b) - k)
    for f in ("o", "h", "l", "c"):
        getattr(out, f)[k:] += bump
    out.h[k:] = np.maximum.reduce([out.o[k:], out.h[k:], out.c[k:]])
    out.l[k:] = np.minimum.reduce([out.o[k:], out.l[k:], out.c[k:]])
    out.v[k:] *= rng.lognormal(0, 1, len(b) - k)
    return out


def test_v1_frame_is_causal():
    b = synth_session(3, minutes=600, theta=0.04, shocks=(Shock(170, 6, -1.0),))
    k = 300
    p = V1Params(session_len=600)
    f0 = run_v1(b, p).frame
    f1 = run_v1(_perturb_after(b, k), p).frame
    # vwap_prev/sigma_prev at bar k use only bars < k; z at k also uses close_k
    np.testing.assert_allclose(f0.vwap_prev[: k + 1], f1.vwap_prev[: k + 1], equal_nan=True)
    np.testing.assert_allclose(f0.sigma_prev[: k + 1], f1.sigma_prev[: k + 1], equal_nan=True)
    np.testing.assert_allclose(f0.z[:k], f1.z[:k], equal_nan=True)


def test_v1_decisions_before_k_unchanged_by_future():
    b = synth_session(5, minutes=600, theta=0.04, shocks=(Shock(170, 6, -1.0), Shock(400, 6, 1.0)))
    k = 350
    p = V1Params(session_len=600)
    e0 = [e for e in run_v1(b, p).events if e[0] < k]
    e1 = [e for e in run_v1(_perturb_after(b, k), p).events if e[0] < k]
    assert e0 == e1


def test_v1_vwap_resets_each_session():
    b = synth_multiday(7, days=3)
    f = run_v1(b, V1Params(session_len=1440)).frame
    starts = np.flatnonzero(np.diff(b.session)) + 1
    assert np.all(np.isnan(f.vwap_prev[starts]))
    assert np.all(np.isfinite(f.vwap_prev[starts + 1]))


def test_vault_vwap_depends_on_history_start():
    b = synth_multiday(7, days=3)
    full = run_vault(b).vwap[2880:]
    late = run_vault(b.slice(2880)).vwap
    assert np.max(np.abs(full - late)) > 0.1


def test_vault_crossunder_semantics():
    c = np.array([100.0] * 25 + [95.0, 94.0, 100.0])
    n = len(c)
    b = Bars(c, c + 0.1, c - 0.1, c, np.ones(n), np.zeros(n, int), np.arange(n))
    vr = run_vault(b)
    assert vr.go_long[25] and not vr.go_long[26]
    assert vr.position[26] == 1


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
