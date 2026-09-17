# JOB-20260917-MM-001 paper regime logger (research only)

Offline/paper harness for the balance-break → confirm → trend-handoff regime logger described in Architecture v0.1. **No live trading, no exchange API keys.**

## Repo layout

```
config/regime_logger.default.yaml   # DRAFT thresholds + split fractions
data/stubs/sample_ticks.csv         # CSV stub for smoke runs
src/regime_logger/                  # Python package (src layout)
tests/                              # pytest unit tests (FSM transitions)
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

## Python API

```python
from regime_logger import RegimeFSM, load_config
from regime_logger.ingest import iter_observations

config = load_config("config/regime_logger.default.yaml")
fsm = RegimeFSM(config)
fsm.run(list(iter_observations("data/stubs/sample_ticks.csv")))
print(fsm.summary_counts())
```
