# JOB-20260917-MM-001 paper regime logger (research only)

Offline/paper harness for the balance-break → confirm → trend-handoff regime logger described in Architecture v0.1. **No live trading, no exchange API keys.**

## Repo layout

```
config/regime_logger.default.yaml   # DRAFT thresholds + split fractions
data/stubs/sample_ticks.csv         # CSV stub for smoke runs
src/regime_logger/                  # Python package (src layout)
  judgment/                         # Judgment battery (Jev-like stubs; no live API)
tests/                              # pytest unit tests (FSM + battery)
```

## State machine

```
BALANCE → BREAK_CANDIDATE → CONFIRM_WINDOW → TREND_HANDOFF
                ↑______________________________|
```

- **Balance (locked):** mid inside session range **and** rolling VWAP band. DOM shelf is confirm-only, not part of the definition.
- **Break candidate:** range **or** VWAP exit with print evidence; quote-walk alone is VETO'd.
- **Confirm (locked):** hold beyond level + reload/aggression + optional print count → `PASS` / `FAIL`.
- **SIG-PULL:** separate boolean; never promotes `TREND_HANDOFF` by itself.

Lucas gates (v0.1): thin-range `R_min` blocks `BREAK_CANDIDATE`; `event_window` defaults confirm to `FLAT_WATCH`; BN labels tagged `venue=BN_AGG proxy=true`.

## Config schema

All thresholds are **DRAFT** — calibrate on the develop split only.

```bash
regime-logger schema
```

Or inspect `config/regime_logger.default.yaml` and `src/regime_logger/config.py`.

## How to run tests

```bash
pip install -e ".[dev]"
pytest -v
```

## How to run the paper harness

```bash
pip install -e .
regime-logger run --data data/stubs/sample_ticks.csv --config config/regime_logger.default.yaml --output-dir output
```

Outputs (under `--output-dir`):

- `regime_transitions.csv` — state transition log (all splits)
- `regime_summary_develop.json` — summary counts on **develop** split only
- `judgment_battery.csv` — parallel judgment battery log (stub Choice/Noul/Score)

## Judgment battery (Prompt D — stubs only)

**No live Jev / no AgenKit / no TypeSafe API keys.** The judgment battery is a paper overlay inspired by the Jev HFT pattern: deterministic code owns the FSM and Lucas hard gates; the battery returns typed stub answers for logging and future calibration.

### Architecture

1. **Hard gates in code first** (Lucas C1–C4, quote-walk VETO) — short-circuit before trusting any battery output.
2. **MarketState snapshot** — JSON schema built from observation + FSM state + gate flags.
3. **StubJudgmentClient** — deterministic Choice / Noul / Score stubs behind a `JudgmentClient` interface (swap for a future TypeSafe client without changing the runner).

### Battery questions (stub answers)

| Type | Question | Range |
|------|----------|-------|
| Choice | `regime` | `BALANCE`, `BREAK_CANDIDATE`, `TREND_HANDOFF`, `FLAT_WATCH` |
| Noul | `toxic_flow` | 0–1 |
| Noul | `liquidity_stressed` | 0–1 |
| Noul | `quote_walk_veto_risk` | 0–1 |
| Score | `quote_environment` | 0–100 |
| Score | `inventory_pressure` | 0–100 |

Each answer includes a `confidence` field (stub). All battery thresholds in config are **DRAFT**.

**SIG-PULL** remains a separate boolean in the FSM; it must **not** alone set `TREND_HANDOFF` in either the FSM or the battery regime Choice.

### How to run battery stubs

```bash
pip install -e ".[dev]"

# Inspect MarketState JSON schema
regime-logger battery-schema

# Run harness (battery enabled by default in config)
regime-logger run --data data/stubs/sample_ticks.csv --config config/regime_logger.default.yaml --output-dir output

# Inspect battery log
head output/judgment_battery.csv
```

Disable the overlay in `config/regime_logger.default.yaml`:

```yaml
judgment_battery:
  enabled: false
  client: stub  # only 'stub' is implemented — no live Jev
```

### Python API (battery)

```python
from regime_logger import JudgmentBattery, load_config
from regime_logger.fsm import RegimeFSM, RegimeState
from regime_logger.ingest import iter_observations

config = load_config("config/regime_logger.default.yaml")
fsm = RegimeFSM(config)
battery = JudgmentBattery(config.judgment_battery, config)

for obs in iter_observations("data/stubs/sample_ticks.csv"):
    fsm.step(obs)
    result = battery.evaluate(obs, fsm.state)
    print(result.regime.value, result.toxic_flow.value, result.hard_gate_short_circuit)
```

## Python API

```python
from regime_logger import RegimeFSM, load_config
from regime_logger.ingest import iter_observations

config = load_config("config/regime_logger.default.yaml")
fsm = RegimeFSM(config)
fsm.run(list(iter_observations("data/stubs/sample_ticks.csv")))
print(fsm.summary_counts())
```
