# HFT-strategies (paper track)

**PAPER / RESEARCH ONLY.** No live trading, no exchange keys, no order placement.

This is a separate paper research track. It does not overlap with the desk's frozen-session VWAP rejection
work (B-01) or the inventory-accumulation work.

| File | What |
|---|---|
| [`vwap_sd_mr_teardown_20261001.md`](vwap_sd_mr_teardown_20261001.md) | Teardown of the vault "VWAP Standard Deviation Mean Reversion" Pine: mechanism map, defects, B-01-style geometry comparison, backlog, paper v1 contract, falsification |
| [`vwap_sd_mr_improved_sketch.md`](vwap_sd_mr_improved_sketch.md) | VSD-MR v1 paper sketch: formulas, defaults, pseudocode, a Pine snippet marked RESEARCH ONLY, open questions |
| [`figures/`](figures/) | fig01–fig07. Every price path is synthetic and educational, not a backtest |
| [`tools/vwap_sd_mr_research.py`](tools/vwap_sd_mr_research.py) | Reference engines: `run_vault` (vault Pine semantics) and `run_v1` (paper contract), plus synthetic generators |
| [`tools/make_figures.py`](tools/make_figures.py) | Regenerates every figure (seeded) |
| [`tools/test_vwap_sd_mr_research.py`](tools/test_vwap_sd_mr_research.py) | Causality and semantics checks |

```bash
pip install numpy matplotlib
python3 desk-briefs/hft-strategies/tools/make_figures.py
python3 desk-briefs/hft-strategies/tools/test_vwap_sd_mr_research.py
```
