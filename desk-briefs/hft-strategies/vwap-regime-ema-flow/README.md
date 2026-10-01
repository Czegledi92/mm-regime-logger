# VWAP regime-follow + EMA 21/50/100 ribbon filter (paper packet)

**PAPER / RESEARCH ONLY.** No live trading, no exchange keys, no order placement, no real market data.
Every figure is a seeded synthetic 5-minute path and is educational, not a backtest.

**Question.** Does session VWAP work as a regime divider (above = bullish, below = bearish), and once a
regime cracks, does "follow the flow" pay? It is tested two ways: (1) lean inventory with the VWAP side,
and (2) trade perps on the VWAP side only while the 21/50/100 EMA ribbon is intact.

**Short answer.** The idea can be written as causal, checkable rules (contract v0). Whether it has edge is
unknown: public evidence for VWAP-side persistence is US-equity-index only and not peer-reviewed. Trade
the AGREE cell only, expect hours of ribbon lag, and run the Phase-0 base-rate study (contract §10) before
any backtest claim.

## Progression on this track

| Step | Packet | Bet | Uses VWAP as |
|---|---|---|---|
| 1 | [`../vwap_sd_mr_teardown_20261001.md`](../vwap_sd_mr_teardown_20261001.md), [`../vwap_sd_mr_improved_sketch.md`](../vwap_sd_mr_improved_sketch.md) | Fade: a stretch to ±k·SD comes back to VWAP | A magnet (mean) |
| 2 | **this packet** | Follow: once price is accepted on one side of VWAP, the side persists; the ribbon confirms | A divider (regime boundary) |

Both bets rest on the same reference level, so a single base-rate dataset (touch-back probability against
side persistence) tests both. The brief's §2 sets out the differences.

## Contents

| File | What |
|---|---|
| [`research_brief_20261001.md`](research_brief_20261001.md) | Market research brief: desk takeaways, VWAP-as-divider evidence, how it differs from SD-MR, VWAP × ribbon confirm/conflict, Book A vs Book B, pitfalls, sources |
| [`paper_rule_contract_v0.md`](paper_rule_contract_v0.md) | VRF-EMA v0 rules: regime, ribbon gate, decision matrix, Book A (inventory skew) and Book B (perp) entry/add/reduce/flat, kill switches, Phase-0 checklist, open questions, Pine visual sketch |
| [`figures/`](figures/) | fig01–fig09 (synthetic, labelled) |
| [`tools/vwap_regime_flow.py`](tools/vwap_regime_flow.py) | Causal reference engine: frozen session VWAP regime, ribbon state machine, Book A and Book B paper runners, synthetic generator |
| [`tools/make_figures.py`](tools/make_figures.py) | Regenerates every figure (seeded) and prints the numbers quoted in the brief |
| [`tools/test_vwap_regime_flow.py`](tools/test_vwap_regime_flow.py) | Causality and rule checks (prefix invariance, VWAP reset, acceptance, EMA seeding, AGREE-only entries, kill timing, session flat) |

## Figures

| | |
|---|---|
| [fig01](figures/fig01_two_regimes.png) | Regime shading: raw VWAP crosses vs accepted regime changes |
| [fig02](figures/fig02_ribbon_intact_vs_tangled.png) | Ribbon intact vs tangled, with the state strip |
| [fig03](figures/fig03_long_above_vwap_bull_ribbon.png) | Annotated long: above VWAP + bull ribbon |
| [fig04](figures/fig04_short_below_vwap_bear_ribbon.png) | Annotated short: below VWAP + bear ribbon |
| [fig05](figures/fig05_conflict_no_trade.png) | Conflict case: below VWAP with a bull ribbon, stay flat |
| [fig06](figures/fig06_decision_matrix.png) | Decision matrix (VWAP side × ribbon state) |
| [fig07](figures/fig07_inventory_book.png) | Book A inventory lean vs neutral market making, with markouts |
| [fig08](figures/fig08_whipsaw_and_null.png) | Whipsaw and null paths: naive vs regime vs regime + ribbon |
| [fig09](figures/fig09_lag_vwap_vs_ribbon.png) | Lag from VWAP crack to ribbon confirmation |

## Run

```bash
pip install numpy matplotlib
python3 desk-briefs/hft-strategies/vwap-regime-ema-flow/tools/make_figures.py
python3 desk-briefs/hft-strategies/vwap-regime-ema-flow/tools/test_vwap_regime_flow.py
```

The engine imports `Bars` from [`../tools/vwap_sd_mr_research.py`](../tools/vwap_sd_mr_research.py), so
keep both packets together.
