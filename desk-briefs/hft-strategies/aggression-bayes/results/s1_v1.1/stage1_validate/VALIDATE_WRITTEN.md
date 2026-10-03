# S1-LXF-BAR v1.1, stage 1: develop and validate results, written down before the test split is touched

**PAPER ONLY.** No orders, no sizing. Written 2026-10-03 at about 12:40 UTC by `code/s1/s1.py --stage validate`. At this point no statistic of the test split (2026-09-01 → 2026-10-01) has been computed or read. The test split is run once, in the next commit, with no code change to the primary analysis.

Inputs: 1,466 files from `data.binance.vision`, every one matching its `.CHECKSUM` (T7). S0 reproduces all 14 known answers (T8). Tests T1–T10 pass (`tests_report.csv`). `CAL=NONE` (no calendar file), `ALGEBRA=RECON`, every gate row `GATE_PARTIAL`.

## Events

| Split | Real events | Real, `CLOCK_OK` | Real, in clusters | Primary placebo events kept after the 10 bp hygiene rule |
|---|---|---|---|---|
| Develop | 3,376 | 2,557 | 97 | 6,323 |
| Validate | 964 | 767 | 39 | 1,855 |

## H1 (level lean)

40 primary cells are populated on develop. Six lean on develop, all RESPECT and all in the UTC box after 360 minutes from the IB end. They are the only cells with n_R + n_B ≥ 100.

| Lean cell (type, box, s, bucket) | Develop n_R / n_B | p̂ | Validate n_R / n_B | Validate share | One-sided p | Validate check |
|---|---|---|---|---|---|---|
| IBH, UTC, +1, 360+ | 124 / 48 | 0.718 | 33 / 16 | 0.673 | 0.011 | Pass |
| IBH, UTC, −1, 360+ | 161 / 47 | 0.761 | 32 / 26 | 0.552 | 0.256 | Fail |
| IBL, UTC, +1, 360+ | 145 / 72 | 0.670 | 36 / 13 | 0.735 | 0.0007 | Pass |
| IBL, UTC, −1, 360+ | 121 / 47 | 0.717 | 37 / 6 | 0.860 | < 0.0001 | Pass |
| IBM, UTC, +1, 360+ | 140 / 59 | 0.702 | 55 / 14 | 0.797 | < 0.0001 | Pass |
| IBM, UTC, −1, 360+ | 135 / 58 | 0.702 | 22 / 13 | 0.629 | 0.088 | Fail |

Still open: H1 passes if any of the four validate-passing cells has a test RESPECT share above 0.5 with n ≥ 15.

**Diagnostic, found before the test split and not part of pass/fail.** Primary placebo levels show the same RESPECT share as real levels. Over all `CLOCK_OK` events with a RESPECT or BREAK label, the share is 0.699 real against 0.705 placebo on develop, and 0.711 against 0.730 on validate. The share is driven by the touch geometry: NEAR touches respect 0.780 (real) and 0.792 (placebo) on develop, PIERCE touches 0.370 and 0.455. So H1's coin-flip null measures the label's barrier asymmetry, not something specific to VWAP or IB levels. Per-cell numbers are in `h1_placebo_diagnostic.csv`.

## H2 (flow confirms more at real levels than at placebos), h = 3 bars

| Split | H | Δ_real (bp) | Δ_placebo (bp) | I (bp) | 97.5% interval for I |
|---|---|---|---|---|---|
| Develop | RESPECT | −0.046 | 0.343 | −0.389 | [−2.146, 1.442] |
| Develop | BREAK | 0.685 | −0.126 | 0.810 | [−2.144, 3.765] |
| Validate | RESPECT | −0.073 | −0.210 | 0.137 | [−2.071, 2.064] |
| Validate | BREAK | −0.696 | −0.042 | −0.654 | [−5.808, 3.802] |

**Already determined: H2 FAILS.** The pass rule needs the lower 97.5% bound above 0 on validate *and* test for the same H. On validate it is −2.071 (RESPECT) and −5.808 (BREAK), and for BREAK Δ_real is also negative.

## G (AGREE events clear fees)

`EDGE_OK` (frozen develop table) passes one lean cell: IBH, UTC, −1, 360+ (32 develop candidates, mean Y_net(3) 2.869 bp, lower 95% bound 0.204). Every AGREE event comes from that cell, and it is one of the two cells that failed the H1 validate check.

| Split | AGREE n | Mean Y_net(3), primary fee (bp) | 95% interval | Lean-cell `FLAT_WATCH` n | Their mean (bp) |
|---|---|---|---|---|---|
| Develop | 36 | 2.723 | [0.323, 5.942] | 1,235 | −0.407 |
| Validate | 16 | 1.587 | [−2.854, 6.787] | 343 | 0.356 |

**Already determined: G FAILS.** It needs n_AGREE ≥ 30 on validate, and validate has 16. Its 95% lower bound is also below 0.

## Decision-table row

- If H1 passes on test: **Pass / Fail / any**. The level leans, but bar flow adds nothing at 1 m. S2 must show the interaction at 1 s before any DOM work is justified.
- If H1 fails on test: **Fail / Fail**. Run placebo diagnostics and S2; hold DOM-study investment until S2 reports.

Either way, the placebo diagnostic above means an H1 pass should not be read as a level-specific lean.

`events.parquet` for develop and validate is not duplicated here. The final run writes every split to `results/s1_v1.1/events.parquet`.
