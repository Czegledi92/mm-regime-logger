# S2-LXT-1S v1.0: level × 1-second tape on public BTCUSDT trades (computable specification)

**PAPER ONLY.** This is a pre-registration. It contains no result. No live orders, no sizing, no DOM. The only numbers in it are parameter choices (pre-registered placeholders) and data facts checked against the public Binance archive (tagged `[ARCHIVE]`, checked 2026-10-03 12:50–13:00 UTC on the develop day 2026-06-30).

Parents: the program ([`20261003-level-x-live-flow-program.md`](20261003-level-x-live-flow-program.md), §5 ladder row S2, §2 pattern catalog, §3.1–3.3), the S1 spec ([`20261003-s1-level-x-bar-flow-spec.md`](20261003-s1-level-x-bar-flow-spec.md) v1.1) and the S1 results ([`results/s1_v1.1/20261003-s1-results.md`](results/s1_v1.1/20261003-s1-results.md)). Where they differ, this file wins for Study 2. Anything not restated here is as in the S1 spec.

Change control: any change to a value in this file creates a new minor version with a written reason. Results from different versions are never pooled.

| Version | Change | Reason |
|---|---|---|
| v1.0 | First computable spec. Develop and validate only | The ladder named S2 but did not specify it. S1 v1.1 reached "H1 Pass, H2 Fail, G Fail", whose decision row says S2 must show the interaction at 1 s before any DOM work |

## 0. What this spec settles that the ladder row left open

| # | Ladder row / program said | This spec | Why |
|---|---|---|---|
| D1 | "`trades` built into 1 s bars; aggTrades for sweep groups only" | 1 s bars **and** sweep groups both come from `trades`. aggTrades are downloaded for one audit day only (§2.3) | On 2026-06-30 every aggTrades sweep (same `transact_time` and side, 2 or more prices) is also a sweep in `trades`, which find 5.5% more (§2.3). aggTrades id ranges also cover ids that `trades` omits, and their per-minute volume does not reconcile with the klines (S1 S0). One tape for bars and sweeps keeps the features on the same prints |
| D2 | "Baseline: S1 bar model on the same episodes; placebo levels" | Episodes are the S1 v1.1 events, unchanged. The S1 lean cells are reused, frozen. The placebo interaction (S1-H2) is rerun at 1 s, and the lift test is also run at placebo levels | S1 found that a test without a fake-level comparison passes on label geometry |
| D3 | Program: decide on a 1 s clock, burst window `w` (proposal 15 s), markout from the end of the burst | Primary clock: decision 15 s after the first touching trade. The S1 minute clock is kept as a pre-registered secondary, so that any change can be traced either to finer information or to an earlier decision | The headline question is whether moving from 1 m to 1 s changes the S1 H2 and G failures |
| D4 | The test split is "touched once" | The 2026-09-01 → 2026-10-01 split is **not part of this run**: no trades file from it is downloaded. Verdicts here are validate-stage. A validate fail is final; a validate pass is provisional | No existing decision table assigns that window to S2, and S1 has already used it. §10.3 lists the options for an S2 test split |

## 1. Question and hypotheses

**Question.** Does moving from 1-minute bars to 1-second tape change the S1 failures of H2 (flow confirms more at real levels than at placebo levels) and G (AGREE events clear fees), or does the same pattern hold?

| ID | Hypothesis | Label | Section |
|---|---|---|---|
| **S2-H2** | A 1 s tape confirmation for hypothesis H predicts H-direction 180 s markouts more at real levels than at placebo levels (positive interaction) | `Y1s^H(180)` | §7, §10 |
| **S2-G** | AGREE events at 1 s (S1 lean cell plus 1 s confirmation plus the computable gate flags) have positive net 180 s markouts at the branch's primary fee | `Y1s_net(180)` | §9, §10 |
| **S2-L** | Tape features add held-out predictive lift over the S1 bar model for the level outcome (ladder pass rule 1) | `Y1s_level` | §10 |

S1-H1 is not retested: S1 v1.1 is accepted as reported, including the caveat that its lean is label geometry.

## 2. Data

### 2.1 Manifest

Base URL `https://data.binance.vision/data/`. Every zip has a `.CHECKSUM` sha256 sibling. A day whose file fails to download or fails its checksum is logged and **dropped as a slice**: its events are excluded (`tape_na`) and no value is filled in.

| Dataset | Path | Use |
|---|---|---|
| Perp `trades` | `futures/um/daily/trades/BTCUSDT/BTCUSDT-trades-{date}.zip` | 1 s bars, sweeps, prints at the level, labels. Columns `id, price, qty, quote_qty, time, is_buyer_maker`, header row, ms timestamps `[ARCHIVE]` |
| Perp 1 m klines, 5 m metrics, spot 1 m | as S1 (already downloaded and checksum-verified by S1) | S1 episode reconstruction, kline reconciliation of every trades day, `oi_d5c` |
| Perp `aggTrades` | `futures/um/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2026-06-30.zip` | Audit day only (§2.3) |

| Window | Dates (inclusive) | Use |
|---|---|---|
| Tape warm-up | 2025-12-12 → 2025-12-31 | Trailing tape distributions only (20 days for same-hour z-scores; 24 h for the burst threshold). No events |
| Develop | 2026-01-01 → 2026-06-30 | Fit the lift models; build the 1 s `EDGE_OK` table |
| Validate | 2026-07-01 → 2026-08-31 | Out-of-sample verdicts |
| Test | 2026-09-01 → 2026-10-01 | **Not downloaded, not used** (D4) |

Size: 263 trades files of 25–50 MB zipped each `[ARCHIVE]`, about 9 GB. Raw data is not committed.

### 2.2 Per-day reconciliation (every trades day)

Every trades day must reconcile with that day's S1 1 m klines in every minute: `volume`, `taker_buy_volume` (sum of `qty` where `is_buyer_maker` is false) and `count`, compared as integer thousandths of a BTC. A day with any mismatching minute is logged and dropped as a slice, like a checksum failure.

### 2.3 S0-T known answers (develop day 2026-06-30, `[ARCHIVE]`)

| Check | Known answer |
|---|---|
| sha256 of `BTCUSDT-trades-2026-06-30.zip` | `042563f0f275523f9513060c5f73526706106ab60daa79bcec992e33492d35c6`, equal to the `.CHECKSUM` |
| Rows; header | 4,297,703 rows; header present |
| Trade-id continuity | 6,088 gaps, the largest step 4. `time` never decreases in id order |
| Against the 1 m klines | 0 of 1,440 minutes mismatch on volume, taker-buy volume or count. Day volume 191,646.301 BTC |
| Seconds with at least one trade | 84,201 of 86,400 |
| Taker groups from `trades` (§5.3) | 890,137 groups, 150,006 sweeps (81,726.879 BTC), 513 sweeps with non-monotone prices |
| aggTrades | 1,596,010 rows; 697 ids inside aggTrades id ranges are absent from `trades` |
| Sweep keys (ms `time`, side) | `trades` 149,281; aggTrades 141,448; **all 141,448 aggTrades keys are found in `trades`** |

## 3. Episodes

- The episodes are the S1 v1.1 events (S1 spec §5, `ALGEBRA=RECON`, `CAL=NONE`), rebuilt with the S1 code from the S1 inputs, restricted to develop and validate. Real events, primary placebos (±25, ±50 bp, hygiene-dropped ones removed) and σ placebos, with their S1 `event_id`, `cluster_id`, `instance_id`, `clock_ok` and level features. The rebuilt rows must equal the committed `results/s1_v1.1/events.parquet` (test T9).
- The S1 develop lean cells and their hypotheses H_L are reused, frozen: six UTC-box, 360+ min, RESPECT cells. They are refit from develop with the S1 code and must equal the committed `h1_cells.csv` lean set.
- The level posterior is frozen at the open of the touch bar t (bars ≤ t−1), as in S1.

## 4. One-second bars and the mid proxy

- Second k covers [1,000·k, 1,000·(k+1)) ms. Per second: trade count, volume, taker-buy volume, first, high, low and last price, the last buyer-initiated price (`is_buyer_maker` false) and the last seller-initiated price.
- **Mid proxy at the end of second k:** the average of the most recent buyer-initiated and seller-initiated trade prices, if both are at most 10 s old and the buyer price ≥ the seller price; otherwise the last trade price. If the last trade is more than 60 s old, the mid proxy is NA. BTCUSDT's 0.1 USDT tick is about 0.01 bp, so bounce bias is small. The median gap between the mid proxy and the last price is reported.

## 5. Touch second, burst window, clocks

### 5.1 Touch

τ is the time of the first trade in the touch bar [`open_time`, `open_time` + 60 s) with s·(p − L)/L × 10⁴ ≤ 5, the S1 touch band. Because the klines reconcile with `trades` exactly, every S1 event has such a trade (test T1). τ_s = ⌊τ / 1,000⌋.

### 5.2 Clocks

| Clock | Window W | Decision time T_d | Status |
|---|---|---|---|
| **B15 (primary)** | Seconds τ_s … τ_s + 14 (15 s, starting with the touch second) | 1,000·(τ_s + 15) | Primary for S2-H2 and S2-G |
| M60 (minute) | Seconds of the touch bar (60 s) | `open_time` + 60 s, the S1 decision time | Primary for S2-L (its baseline is the S1 bar model, which is only known at the minute close). Secondary for S2-H2 and S2-G |
| B5, B30, B60 | As B15 with w = 5, 30, 60 s | 1,000·(τ_s + w) | Robustness |

The window never starts before the freeze (`open_time` ≤ τ_s·1,000), so level and burst data stay disjoint.

### 5.3 Taker groups and sweeps

A taker group is a maximal run of trades, in id order, with the same ms `time` and the same `is_buyer_maker`; id gaps do not split it. A **sweep** is a group that fills at 2 or more distinct prices. The side **into the level** is selling (`is_buyer_maker` true) for s = +1 and buying for s = −1. A group belongs to W if its `time` is in W.

## 6. Tape features (trades in W only, all known at T_d)

| Feature | Definition |
|---|---|
| `TI_w` | (taker buy qty − taker sell qty) / qty over W. `TI_into_w` = −s·`TI_w` |
| `v_w`, `n_w` | Volume and trade count in W |
| `vz_w`, `nz_w`, `atsz_w` | Robust z-scores ((x − median) / (1.4826·MAD)) of ln `v_w`, ln `n_w` and ln(`v_w`/`n_w`) against grid-aligned blocks of the same length in the same UTC hour over the 20 calendar days before the event day. Blocks with no trades are left out of the reference |
| `cl_w` | s·(P_last − L)/L × 10⁴, with P_last the last trade price in W. Negative means beyond the level |
| `pen_w` | max over trades in W of −s·(p − L)/L × 10⁴ |
| `at_level_qty`, `at_level_share` | Qty of trades in W with \|p − L\|/L × 10⁴ ≤ 1, and its share of `v_w` |
| `sweep_into_n`, `sweep_into_share` | Sweeps into the level in W, and their qty share of `v_w` |
| `sweep_away_n` | Sweeps in the other direction in W |
| `sweep_through` | 1 if a sweep into the level has any fill beyond L (s·(p − L) < 0) |
| `ti_last5_into` | `TI_into` over the last 5 s of W |
| `absorb` | Absorption proxy (program §2, adapted from ticks to bp): `TI_into_w` ≥ 0.6 and `vz_w` ≥ 1 and `pen_w` ≤ 1 bp and `cl_w` ≥ 0 |
| `burst_into` | Bid-hit / offer-lift burst (program §2): \|Σ signed qty over W\| ≥ the 95th percentile of the rolling w-second \|Σ signed qty\| over the 86,400 s before W, and \|`TI_w`\| ≥ 0.6. +1 if into the level, −1 if away, 0 otherwise |
| `sbr` | Side being run (program `EDGE_OK` (a)), in the last 5 s of W. For H = RESPECT: `TI_into` ≥ 0.20 there and some trade there beyond L by ≥ 2 ticks (0.2 USDT). For H = BREAK: `TI_into` ≤ −0.20 there and some trade there back on the approach side by ≥ 2 ticks |
| `oi_d5c_w` | As S1 `oi_d5c`, with T_d as the decision time |

## 7. One-second burst classification (pre-registered thresholds, not fitted)

| | Condition |
|---|---|
| `confirm1s_RESPECT` | `TI_into_w` ≥ 0.20 and `cl_w` ≥ 0 and `vz_w` ≥ 0 and `sweep_through` = 0 (aggression into the level that fails to progress through it) |
| `confirm1s_BREAK` | `TI_into_w` ≥ 0.20 and `cl_w` < 0 and `vz_w` ≥ 0 and `sweep_into_n` ≥ 1 (prints through the level, with a taker walking the book) |
| `veto1s_RESPECT` | `TI_into_w` ≥ 0.20 and `cl_w` < −5 |
| `veto1s_BREAK` (`ABSORB_VETO`) | `absorb` |
| `LIQ_VETO_5m` | `oi_d5c_w` < 0 and \|`TI_w`\| ≥ 0.20 |

**Bar-analogue rule (secondary).** The S1 rule applied to W: confirm without the sweep conditions, S1 vetoes, and `PRINT_CONFIRM` as `vz_w` ≥ 0. On clock M60 it uses the same prints as S1, so its H2 differs from S1's only through the label.

## 8. Labels (the 1 s mid proxy, read only after T_d)

- Entry is the mid proxy at the end of second T_d/1,000, which is 1 s after the decision (a latency allowance; robustness: 0 s). Exit is the mid proxy h seconds later, h ∈ {30, 60, 180, 300, 900}. **h = 180 is primary.**
- `Y1s^H(h)` = dir(H)·ln(exit / entry) × 10⁴, with dir(RESPECT) = +s and dir(BREAK) = −s. NA if either mid is NA or its day was dropped.
- `Y1s_net` = `Y1s` − f, with f ∈ {0, 1.09, 2.18} bp. Primary fee: RESPECT (branch B) 0, BREAK (branch A) 1.09. All three are always reported.
- `Y1s_level`: first passage of the per-second mid proxy over seconds from entry to entry + 1,800. RESPECT if s·(mid − L)/L × 10⁴ ≥ +10 comes first, BREAK if ≤ −10, NONE otherwise.

## 9. The gate at 1 s (every row tagged `GATE_PARTIAL`; names and order locked)

| Flag | S2 computation | Not testable |
|---|---|---|
| `CLOCK_OK` | S1 `clock_ok` (the touch bar's) | none |
| `INDEPENDENT_AGREE` | H_L ≠ NONE (S1 lean cell) and no cluster conflict, then `confirm1s_{H_L}`, no `veto1s_{H_L}`, no `LIQ_VETO_5m`, `EPISODE_ONCE`. Clusters, representatives and spending as in S1 | `LIQ_VETO` at burst scale (5 m OI only) |
| `PRINT_CONFIRM` | Real prints at the level: `at_level_qty` > 0 or `sweep_through` = 1. For H = BREAK, `ABSORB_VETO` (`absorb`) fails it | Quote-walk and `SPOOF_PULL_VETO` (no quotes, no DOM) |
| `DEPTH_AGREE` | Pass-through, flagged `NT` | All of it |
| `EDGE_OK` | (a) Side being run: `sbr` for H_L fails it. (b) The frozen table: the cell's develop lower 95% bound of `Y1s_net(180)` at the primary fee, over develop events that pass every earlier flag, is > 0 | True mid |

AGREE means every computable flag passes; otherwise `FLAT_WATCH` with the first failing flag. The S1 lean cells are all RESPECT, so every possible AGREE is branch B at the 0 bp maker placeholder. **S2 has no fill model**: the markout assumes a fill at the mid proxy.

## 10. Statistics, pass and fail

Statistics use `CLOCK_OK` events only (S1 §10), per split, with the S1 day-block bootstrap (B = 2,000, seed 20261003, one weight matrix per split, shared by real and placebo statistics, percentile intervals).

### 10.1 Rules

| ID | Statistic | Validate-stage **PASS** (all conditions) | **FAIL** |
|---|---|---|---|
| **S2-H2** | S1-H2 on clock B15 with `confirm1s` and `Y1s(180)`: Δ_real(H), Δ_plac(H) over pooled primary placebos, I(H) = Δ_real − Δ_plac | For the same H on validate: lower bound of the 97.5% interval for I(H) > 0 and Δ_real(H) > 0 | Otherwise. A validate fail is final |
| **S2-G** | AGREE events on clock B15: mean `Y1s_net(180)` at the primary fee, with lean-cell `FLAT_WATCH` events for comparison | On validate: n_AGREE ≥ 30, mean > 0, lower 95% bound > 0, no UTC hour supplying more than 50% of Σ`Y1s_net(180)`. The month rule and the test-split conditions (n ≥ 15, mean > 0) wait for an S2 test split | Any validate condition fails. Final |
| **S2-L** | Clock M60. Logistic regression (L2, C = 1.0, numeric features standardised on develop, NA set to the develop median), fit on develop real `CLOCK_OK` events with `Y1s_level` ∈ {RESPECT, BREAK}. M1 (the S1 bar model) uses the S1 logistic cross-check features (level type, box, s, `tsib_bucket`, UTC hour and day of week as one-hot; `speed15`, `dist_vwap_sigma`, `ib_width_rel`, `vwap_slope30`, `touch_seq`) plus the S1 burst features (`TI_into`, `cl_t`, `vz_t`, `pen_t`, `atsz_t`, sign of `oi_d5c`). M2 = M1 plus the tape features of the touch minute (`sweep_into_n` and `sweep_away_n` as log(1 + n), `sweep_into_share`, `sweep_through`, `at_level_share`, `absorb`, `burst_into`, `nz_w`, `ti_last5_into`). ΔLL = mean validate log loss of M1 minus that of M2 | Lower bound of the 95% interval for ΔLL > 0 | Otherwise. Final |

The Brier difference is always reported next to ΔLL. **Fake-level comparison for S2-L:** the same two models are fit and scored on primary placebo events, and ΔLL_real − ΔLL_plac is reported with its interval. If S2-L passes but that interval contains 0, the write-up must read it as "tape adds lift near any price, not at levels".

Power (always reported): episodes per group, and the minimum detectable I(H) ≈ 2.8 × bootstrap SE.

### 10.2 Decision table (validate stage)

| S2-H2 | S2-G | S2-L | Next action |
|---|---|---|---|
| Fail | Fail | Fail | The S1 pattern holds at 1 s. Keep the bar model; per the ladder, DOM work must beat S1, not S2. Desk Floor should weigh the program's P1 restatement (a flow model with a session filter) before funding S3. No S2 test split is needed |
| Fail | Fail | Pass | Tape predicts the outcome better than bars, but not level-specifically (H2) and not after fees (G). The fake-level comparison decides whether the lift is level-specific. A flow-only study candidate, not a gate change |
| Pass | Fail | any | Level-specific flow exists at 1 s but does not clear fees at 180 s. Ask Desk Floor for an S2 test split to confirm H2; fee work moves to S2b/S3 (depth for branch B fills) |
| Pass | Pass | any | Ask Desk Floor for an S2 test split. S2b and S3 design use the S2 rules as the baseline |
| Fail | Pass | any | AGREE events clear fees but flow is not level-specific. Treat as fragile (the S1 lesson). The fake-level G comparison (§11, X3) decides; a test split only with Desk Floor sign-off |

### 10.3 S2 test split (not in this run)

Options for Desk Floor: (i) the S1 test window 2026-09-01 → 2026-10-01, already used once by S1, so S2 statistics there would not be blind to S1's test results; or (ii) a forward window from 2026-10-02 once it is archived. Either way it is touched once, after this run's validate results are committed.

## 11. Secondary analyses (pre-registered, reported, never pass/fail)

| Row | Definition |
|---|---|
| X1 Clock × rule grid | S2-H2 and S2-G statistics on {B15, M60} × {1 s rule, bar-analogue rule}. The M60 × bar-analogue cell is S1's rule on 1 s labels |
| X2 S2-L on clock B15 | M1 = S1 level features plus the bar-analogue features of W (`TI_into_w`, `cl_w`, `vz_w`, `pen_w`, `atsz_w`, sign of `oi_d5c_w`); M2 = M1 plus the tape features of W; labels from the B15 entry |
| X3 Fake-level G | Primary placebo `CLOCK_OK` events whose parent cell key is an `EDGE_OK` lean cell, passing `confirm1s`, no veto, no `LIQ_VETO_5m`, `PRINT_CONFIRM` and `sbr`, with no clusters or `EPISODE_ONCE`. Mean `Y1s_net(180)` at 0, 1.09 and 2.18 bp, against real events under the same reduced rules |
| X4 Horizons | S2-H2 and S2-G at 30 s, 60 s, 5 m and 15 m |
| X5 Pre-`EDGE_OK` candidates | Real events passing every flag before `EDGE_OK`, per split, at the three fees |

## 12. Robustness (reported, never pass/fail)

W = 5, 30, 60 s; at-level band ±2 bp; mid proxy = last trade price; entry latency 0 s; `TI_into_w` threshold 0.10 and 0.30; σ placebos; clusters excluded.

## 13. Outputs (`desk-briefs/hft-strategies/aggression-bayes/results/s2/`)

| File | Content |
|---|---|
| `inputs_manifest.csv`, `tape_qc.csv` | Every trades file: URL, sha256, status; per day: rows, id gaps, kline mismatches, seconds with trades, slice kept or dropped |
| `s0_tape.csv`, `tests_report.csv` | §2.3 and §14 |
| `episodes.parquet` | One row per develop or validate event: S1 keys, tape features for each clock, labels, flags |
| `h2_interaction.csv`, `edge_table.csv`, `gate_log.parquet`, `gate_summary.csv`, `g_stats.csv`, `lift.csv` | Primary rows |
| `grid.csv`, `fake_level_g.csv`, `horizons.csv`, `candidates.csv`, `robustness.csv` | §11 and §12 |
| `summary.json`, `YYYYMMDD-s2-results.md` | Verdicts; the write-up opens with the decision-table row reached and answers the §1 question |

## 14. Tests that must pass before results are read

| Test | Assertion |
|---|---|
| T1 Touch trade | Every develop and validate S1 event has a touching trade in its touch bar |
| T2 Minute equals S1 | On clock M60, `TI_w`, `pen_w` and `cl_w` equal S1's `TI_t`, `pen_t` and `cl_t` for every event (TI exactly in integer thousandths; the others to 10⁻⁹) |
| T3 No look-ahead | Perturbing trades at or after T_d leaves every feature unchanged; perturbing trades before the entry second leaves every label unchanged (one develop day) |
| T4 S0-T | The §2.3 known answers are reproduced exactly |
| T5 Checksums | Every trades file used matches its `.CHECKSUM`; failures are logged and their days dropped |
| T6 Reconciliation | Every trades day used has 0 mismatching minutes against the 1 m klines |
| T7 Determinism | Two runs give byte-identical CSV outputs |
| T8 Placebo hygiene | Inherited from S1 (no placebo within 10 bp of a real level) |
| T9 S1 episodes | Rebuilt develop and validate events equal `results/s1_v1.1/events.parquet` on `event_id`, `open_time`, `L`, `s`, `kind`, `clock_ok`, `Y_level` and `Y_fwd_3` |
| T10 No test split | No trades file dated 2026-09-01 or later is requested, and no test-split event enters any frame |

## 15. What S2 cannot say

- **No quotes, no DOM.** Quote-walk, spoofing, `DEPTH_AGREE` and true-mid markouts stay untestable. The mid proxy comes from trade prices.
- **No fill model.** Branch B's 0 bp maker fee assumes a fill at the mid proxy; queue position and trade-through are S4's job.
- **Coarse OI.** `LIQ_VETO` uses 5-minute OI against a 15 s burst, a resolution mismatch the program already flags.
- **Episodes are S1's.** Touches are still detected on 1 m bars, so a touch that S1's arming rule missed is missed here too.
- **Scope of a pass.** A validate pass is provisional until an S2 test split confirms it.
