# S1-LXF-BAR v1.1: level × bar-flow Bayes on public BTCUSDT klines (computable specification)

**PAPER ONLY.** This is a pre-registration, and it has **not been run**. It contains no result. The only numbers in it are parameter choices (labelled pre-registered defaults) and data facts checked by this run against the public Binance archive (tagged `[ARCHIVE]`, checked 2026-10-02 22:06–22:40 UTC).

Parent program: [`20261003-level-x-live-flow-program.md`](20261003-level-x-live-flow-program.md). Where the two differ, this file wins for Study 1.

Change control: any change to a value in this file creates a new minor version with a written reason. Results from different versions are never pooled.

| Version | Change | Reason |
|---|---|---|
| v1.0 | First computable spec | Next run computes Study 1 from public klines |
| v1.1 | Adds robustness rows R-OI, R-REGIME and R-STOP to §11 and the `regime_tag` column to §12. No pass/fail rule, threshold or definition changed, so v1.0 and v1.1 primary results are identical by construction. Write outputs to `results/s1_v1.1/` | [Iteration 01](20261003-iter01-gate-after-1002-stills.md), changes C2, C5 and C7, after the 2 Oct stills |

## 0. Three corrections to the program's S1 summary

| # | Was | Now | Why |
|---|---|---|---|
| R1 | Penetration depth of the touch (the 0–5 bp "kiss" class) treated as part of the level state | Penetration is a **burst** feature | It is measured on the touch bar itself. Under `INDEPENDENT_AGREE`, the level posterior must be frozen before the burst. So the `[BAYES-0102]` kiss finding cannot sit inside the frozen level prior |
| R2 | H2 measured as P(respect or break), with the outcome window including the touch bar | H2 and the gate test use **forward returns from the next bar's open** (`Y_fwd`) | A level outcome that includes the touch bar's close is partly *made* by the burst. A "close beyond the level" confirm would then predict BREAK mechanically |
| R3 | S0 pass rule: per-minute aggTrades volume equals the kline fields to rounding | Per-minute bucketing must use the **`trades`** file. aggTrades are for sweep detection only | On 2026-10-01, `trades` reconciles exactly with the 1 m klines in every minute; `aggTrades` does not (§2.2) `[ARCHIVE]` |

## 1. Question and hypotheses

**Question.** At frozen session VWAP and finished-IB levels of BTCUSDT perp, are there pre-burst level states that lean toward RESPECT or BREAK? And does touch-minute taker flow confirm the frozen hypothesis better at real levels than at placebo levels?

| ID | Hypothesis | Label | Section |
|---|---|---|---|
| **H1** | Some primary level cells lean: \|P(RESPECT) − 0.5\| ≥ 0.05, out of sample | `Y_level` | §6, §9 |
| **H2** | A bar-flow confirmation pattern for hypothesis H predicts H-direction forward returns more at real levels than at placebo levels (positive interaction) | `Y_fwd(3)` | §7, §10 |
| **G** | AGREE events (lean cell plus confirmation plus the computable gate flags) have positive net 3-minute forward returns at the branch's primary fee | `Y_net(3)` | §8, §10 |

## 2. Data

### 2.1 Manifest

Base URL: `https://data.binance.vision/data/`. Every zip has a sibling `<file>.zip.CHECKSUM` containing a sha256. Verify each file and drop the whole day on a mismatch `[ARCHIVE]`.

| Dataset | Path template | Header row? | Time unit | Notes `[ARCHIVE]` |
|---|---|---|---|---|
| Perp 1 m klines (**primary**) | `futures/um/daily/klines/BTCUSDT/1m/BTCUSDT-1m-{YYYY-MM-DD}.zip` | **Yes** | ms | 1,440 rows a day. Columns: `open_time, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_volume, taker_buy_quote_volume, ignore` |
| Perp 5 m klines (robustness only) | `futures/um/daily/klines/BTCUSDT/5m/BTCUSDT-5m-{date}.zip` | Yes | ms | Same columns |
| Perp metrics (OI) | `futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-{date}.zip` | Yes | string `YYYY-MM-DD HH:MM:SS`, read as UTC | 288 rows a day, **not stored in time order**: sort by `create_time`. Use `sum_open_interest` (BTC) |
| Spot 1 m klines (control) | `spot/daily/klines/BTCUSDT/1m/BTCUSDT-1m-{date}.zip` | **No** | **µs** (16 digits). Divide by 1,000 to get ms | Same 12 columns, in the same order |
| Perp trades (S0 only) | `futures/um/daily/trades/BTCUSDT/BTCUSDT-trades-{date}.zip` | Yes | ms | `id, price, qty, quote_qty, time, is_buyer_maker` |
| Event calendar (optional) | Richard's `calendar/events.csv`: `event_id, ts_utc, name, tier, pre_min, post_min` | Yes | UTC | If absent: `CAL=NONE` (§4.5) |
| Bayes brief (optional) | `cash_vwap_level_bayes_20261002.md` | | | If absent: `ALGEBRA=RECON` (§6.4) |

| Window | Dates (inclusive) | Use |
|---|---|---|
| Warm-up | 2025-10-01 → 2025-12-31 | Trailing distributions only (volume baseline, impulse percentiles, IB-width median). **No events are scored** |
| Develop | 2026-01-01 → 2026-06-30 | Fit the level model, fix tercile cut points, build the `EDGE_OK` table |
| Validate | 2026-07-01 → 2026-08-31 | Out-of-sample check |
| Test | 2026-09-01 → 2026-10-01 | Touched **once**, after validate results are written down |

Size: about 366 days of perp 1 m files (about 60 KB each), spot 1 m and metrics (about 12 KB each). Well under 100 MB in total.

### 2.2 S0 known answers (must reproduce before any S1 result is read)

| Check | Known answer on 2026-10-01 `[ARCHIVE]` |
|---|---|
| sha256 of `BTCUSDT-1m-2026-10-01.zip` (perp) | `062f32fefdfb1d1cfbb6d58ee04c28dd6c45dbf2b52ed60fa4ad6a27b0b19bc5`, equal to the `.CHECKSUM` |
| Perp `trades`, bucketed by `time // 60000`, against the 1 m klines | 0 of 1,440 minutes mismatch on `volume`, `taker_buy_volume` (sum of `qty` where `is_buyer_maker == false`) or `count`. Day volume **143,164.950 BTC**. Trade rows 3,249,979, equal to the sum of kline `count` |
| Perp `aggTrades`, bucketed by `transact_time // 60000`, against the 1 m klines | Day totals equal. Per minute: **139** minutes mismatch on volume (largest gap 3.863 BTC), 90 on taker-buy volume, 49 on open. Trade-ID ranges (`first_trade_id`..`last_trade_id`) cover 730 IDs that are absent from `trades`. Conclusion: aggTrades are not used for per-minute or per-second bucketing |

Consequence for S1: kline `taker_buy_volume` is the exact taker-buy sum of the public trade tape. The S1 flow features below are therefore exact at 1 m, not an approximation.

## 3. Bars, notation, missing data

- A bar is identified by `open_time` (ms, UTC) and covers [`open_time`, `open_time` + 60,000). Its fields are `O, Hi, Lo, C, v` (BTC volume), `tbv` (`taker_buy_volume`) and `n` (`count`). The letter `L` is reserved for a level value.
- The **decision time** of bar t is its close, `open_time + 60,000`. Anything indexed ≤ t is known at decision time; anything ≥ t+1 is future.
- The typical price is TP = (Hi + Lo + C) / 3.
- **Missing bars.** If the expected `open_time` sequence has a gap inside a box, that box is **invalid from the gap onward**: no events, and levels are not updated. If any IB bar is missing, the whole box is invalid. Zero-volume bars are allowed, but a zero-volume touch bar is not an event.
- bp means basis points of the frozen level value: x bp = x × 10⁻⁴ × L.

## 4. Clocks, boxes, levels

### 4.1 Boxes

| Box | Days | Anchor `A` | End | IB |
|---|---|---|---|---|
| **UTC** | Every calendar day | 00:00 UTC | 00:00 UTC next day | [A, A + 60 m) |
| **NY** | NYSE trading days: weekdays excluding 2025-11-27, 2025-12-25 (warm-up), 2026-01-01, 2026-01-19, 2026-02-16, 2026-04-03, 2026-05-25, 2026-06-19, 2026-07-03, 2026-09-07 | 09:30 America/New_York, via the tz database (`zoneinfo`). That is 14:30 UTC until 2026-03-06, 13:30 UTC from 2026-03-09, and 13:30 UTC in Oct 2025 until 2025-10-31, 14:30 UTC from 2025-11-03 | 16:00 America/New_York. Early closes are ignored in v1 | [A, A + 60 m) |

Both boxes are evaluated concurrently and independently; every level belongs to exactly one box. Robustness variant `BOX=EXCLUSIVE`: during NY box hours, only NY levels are eligible.

### 4.2 Eligible event window per box

An event may occur only at bars with `open_time` ∈ [A + 75 m, End − 30 m). The 15 minutes after the IB are the arming lookback (§5.1), and no entries are allowed in the last 30 minutes. For the NY box this means 10:45–15:30 ET.

### 4.3 Levels (frozen at t−1)

| Level | Value used at bar t |
|---|---|
| `VWAP` | VWAP_b(t) = Σ TP_i·v_i / Σ v_i over bars i in box b with i ≤ t−1 |
| `IBH` | max Hi over the 60 IB bars (constant after the IB ends) |
| `IBL` | min Lo over the 60 IB bars |
| `IBM` | (IBH + IBL) / 2 |

Residual dispersion: σ_b(t) = sqrt( Σ v_i (TP_i − VWAP_b(t))² / Σ v_i ) over bars i in box b with i ≤ t−1, floored at 1 bp of VWAP_b(t).

### 4.4 Impulse kill (causal; proposal for Macro, pre-registered as v1)

For box b on day D, the trailing reference set is the 60 most recent valid boxes of the **same type**, strictly before D.

| Trigger | Statistic | Threshold | Effective |
|---|---|---|---|
| I1 | \|ln(C of the last IB bar / O of the first IB bar)\| | ≥ 90th percentile of the reference set | From IB end (A + 60 m) to box end |
| I2 | (IBH − IBL) / IBM | ≥ 90th percentile of the reference set | From IB end to box end |
| I3 | \|ln(C_t / C_{t−1})\| for a bar t after IB end | ≥ 99.9th percentile of all perp 1 m absolute log returns in the 30 calendar days before D | From the decision at bar t to box end |

### 4.5 Event windows

- `CAL=FILE` (preferred): a bar is inside an event window if [`open_time`, `open_time` + 30 m) intersects [ts − pre_min, ts + post_min] for any calendar event.
- `CAL=NONE` (fallback): no event windows. Results carry the tag `CAL=NONE`.
- `CAL=PROXY` (robustness only): on weekdays, exclude bars whose [`open_time`, +30 m) intersects 08:15–09:15 or 13:45–14:45 America/New_York.

### 4.6 `CLOCK_OK` at bar t

`CLOCK_OK(t, b)` holds when all of the following are true: box b is valid at t; t is inside the §4.2 window; the IB has finished (true by construction); the level is box b's own VWAP or IB (true by construction); t is outside every event window; and no impulse trigger has fired for b at or before t.

## 5. Arming, events, instances

### 5.1 Approach side and distance

- Approach side: s = +1 if C_{t−1} > L_{t−1}; s = −1 if C_{t−1} < L_{t−1}. If they are equal, there is no event at t.
- Distance of bar i to level L_i on side s: for s = +1, d_i = (Lo_i − L_i) / L_i × 10⁴; for s = −1, d_i = (L_i − Hi_i) / L_i × 10⁴. A positive d_i means the bar stayed d_i bp away on the approach side; d_i ≤ 0 means the bar reached or crossed the level.

### 5.2 Arming

| Level type | Armed at bar t on side s when |
|---|---|
| `IBH`, `IBL`, `IBM` | For every bar i in [t−15, t−1]: i is in box b, `open_time_i` ≥ A + 60 m, i is on side s, and d_i > 5 bp |
| `VWAP` | For every bar i in [t−15, t−1]: i is in box b, i is on side s, and d_i > max(10 bp, 0.5·σ_b(i)/L_i × 10⁴), using that bar's own frozen VWAP and σ |

### 5.3 Touch event

An event fires at bar t when the level is armed on side s at t and d_t ≤ 5 bp. In words: the touch bar comes within 5 bp of the level, or through it.

Penetration is p_t = −d_t (bp; positive means the bar traded through the level). It is a **burst** feature (R1):

| Class | Range |
|---|---|
| `NEAR` | −5 ≤ p_t < 0 |
| `KISS` | 0 ≤ p_t ≤ 5 |
| `PIERCE` | p_t > 5 |

### 5.4 Instances, `EPISODE_ONCE`, clusters

- **IB instances:** one instance per (box, day, level type). Re-touches after re-arming are new **events** on the same instance; the feature `touch_seq` counts the prior events on that instance.
- **VWAP instances:** each arming under §5.2 opens a new instance. That is the program's VWAP re-arm proposal made concrete (15 bars at max(10 bp, 0.5σ) or more).
- **`EPISODE_ONCE` (gate only):** at most one AGREE per instance. All events still count in H1 and H2 estimation.
- **Clusters:** if events fire at the same bar t on two or more levels (any box) whose values lie within 5 bp of each other, they form one cluster with a `cluster_id`. Clusters are always counted as a single gate event. If the members' frozen hypotheses disagree, the cluster is `FLAT_WATCH` (cluster conflict). H1 counts each member, flagged; a robustness run excludes clusters.

## 6. Level side: frozen state and the level label

### 6.1 Level-state features (bars ≤ t−1 only)

| Feature | Definition |
|---|---|
| `level_type` | VWAP, IBH, IBL, IBM |
| `box` | UTC, NY |
| `s` | approach side |
| `tsib_bucket` | Minutes from IB end to `open_time_t`: [15, 120), [120, 360), [360, ∞). The NY box only populates the first two |
| `speed15` | s·(C_{t−16} − C_{t−1}) / L_{t−1} × 10⁴, positive when moving toward the level. Terciles cut on develop events and frozen |
| `dist_vwap_sigma` | (C_{t−1} − VWAP_b(t)) / σ_b(t) |
| `ib_width_rel` | ((IBH − IBL) / IBM) divided by the median of the same ratio over the previous 20 boxes of the same type |
| `vwap_slope30` | (VWAP_b(t) − VWAP_b(t−30)) / L_{t−1} × 10⁴ |
| `touch_seq` | Prior events on the same instance (IB) or in the same box (VWAP) |
| `hour_utc`, `dow` | calendar |

**Primary cells:** `level_type` × `box` × `s` × `tsib_bucket`. That is 48 cells, 40 of them populated, because the NY box has no third bucket. **Secondary cells** add the `speed15` tercile; they are exploratory and use partial pooling.

### 6.2 Level label `Y_level` (for H1)

First passage on **closes** over bars j = t, …, t+29. The touch bar is included, which is legitimate here because no feature of bar t enters the level posterior:

- `RESPECT` if s·(C_j − L_t)/L_t × 10⁴ ≥ +10 occurs first;
- `BREAK` if s·(C_j − L_t)/L_t × 10⁴ ≤ −10 occurs first;
- `NONE` if neither occurs by t+29;
- NA if any of those bars is missing.

Using closes means a single bar can never satisfy both conditions, so no intrabar ordering is needed.

### 6.3 Level model

- Per primary cell c on develop: n_R and n_B (NONE excluded; its share is reported).
- Empirical-Bayes beta-binomial, pooled within `level_type`: the prior Beta(α, β) is fitted by method of moments across that type's cells. The posterior mean is p̂_c = (n_R + α) / (n_R + n_B + α + β).
- A cell **leans** if it passes H1 on develop (§10). Its frozen hypothesis is H_L = RESPECT if p̂_c > 0.5, else BREAK. Every other cell has H_L = NONE.
- Cross-check: L2 logistic regression (C = 1.0) of R vs B on all §6.1 features, fit on develop. Report validate log loss against the beta-binomial model and against a constant 0.5.
- Calibration: on validate, observed RESPECT share in 5 equal-count bins of p̂.

### 6.4 Event algebra version

`ALGEBRA=RECON` is everything in §5 and §6.2 (5 bp touch band, r = 10 bp, H = 30 bars). `ALGEBRA=BRIEF` replaces the touch band, the classes, r and H with the definitions in `cash_vwap_level_bayes_20261002.md`, and writes a mapping table (brief term to this spec's term) into the output. The two versions are never pooled.

## 7. Flow side: burst features and the forward label

### 7.1 Burst features (bar t only, known at its close)

| Feature | Definition |
|---|---|
| `TI_t` | (2·tbv_t − v_t) / v_t, in [−1, 1] |
| `TI_into` | −s·`TI_t`. Positive means aggressors are pushing into or through the level from the approach side |
| `pen_t`, `pen_class` | §5.3 |
| `cl_t` | s·(C_t − L_t)/L_t × 10⁴. Positive means the bar closed back on the approach side; negative means it closed beyond the level |
| `vz_t` | (ln v_t − median of ln v) / (1.4826 · MAD of ln v), over bars of the same UTC hour in the 20 calendar days before the day of t |
| `atsz_t` | The same robust z-score applied to v/n (average trade size) |
| `oi_d5c` | Causal OI change: OI at the last metrics stamp ≤ the decision time, minus OI at the stamp 5 minutes before it. NA if either is missing |
| `TI_spot_t` | `TI_t` computed from the spot kline at the same `open_time` (control) |

### 7.2 Burst classification relative to hypothesis H (pre-registered thresholds, not fitted)

| | Condition |
|---|---|
| `confirm_BREAK` | `TI_into` ≥ 0.20 and `cl_t` < 0 and `vz_t` ≥ 0 |
| `confirm_RESPECT` | `TI_into` ≥ 0.20 and `cl_t` ≥ 0 and `vz_t` ≥ 0 |
| `veto` for H = BREAK | `TI_into` ≥ 0.20 and `cl_t` ≥ 0 (aggression absorbed; the bar-resolution analogue of `ABSORB_VETO`) |
| `veto` for H = RESPECT | `TI_into` ≥ 0.20 and `cl_t` < −5 (closed through by more than 5 bp) |
| `LIQ_VETO_5m` | `oi_d5c` < 0 and \|`TI_t`\| ≥ 0.20. NA means no veto, flagged as `oi_na` |
| `neutral` | None of the above |

### 7.3 Forward label `Y_fwd` (for H2 and G)

- Entry is at O_{t+1} (decide at the close of t, fill at the next open; the VRF-EMA convention). Exit is at C_{t+h}, for h ∈ {3, 5, 15, 30} bars. h = 3 is the 180 s proxy: from the open of t+1 to the close of t+3 is 3 minutes.
- Direction: dir(RESPECT) = +s; dir(BREAK) = −s.
- Y_fwd^H(h) = dir(H) · ln(C_{t+h} / O_{t+1}) × 10⁴, in bp. NA if any bar from t+1 to t+h is missing. Labels may run past the box end.
- Net of fees: Y_net = Y_fwd − f, with f ∈ {0, 1.09, 2.18} bp per round trip (maker/maker; one taker side; taker/taker). **Primary fee:** RESPECT (branch B) uses 0; BREAK (branch A) uses 1.09. 2.18 is always reported alongside.

## 8. The gate at bar resolution (every row tagged `GATE_PARTIAL`)

| Flag | S1 computation | Not testable in S1 |
|---|---|---|
| `CLOCK_OK` | §4.6 | none |
| `INDEPENDENT_AGREE` | H_L ≠ NONE (lean cell, frozen from develop) **and** `confirm_{H_L}` **and** no `veto` for H_L **and** no `LIQ_VETO_5m` **and** `EPISODE_ONCE` **and** no cluster conflict | `LIQ_VETO` at burst scale (5 m OI only) |
| `PRINT_CONFIRM` | Proxy: the event exists (the bar came within 5 bp) and `vz_t` ≥ 0 | Quote-walk, full `ABSORB_VETO`, `SPOOF_PULL_VETO` |
| `DEPTH_AGREE` | Pass-through, flagged `NT` | All of it |
| `EDGE_OK` | Proxy: the cell's develop-split lower 95% bound of Y_net(3), at the branch's primary fee, is > 0 (a frozen table) | Side-being-run |

**AGREE** = every computable flag passes. Otherwise the row is `FLAT_WATCH`, with the first failing flag as the reason code.

## 9. Placebo levels

- **Primary placebos:** fixed offsets o ∈ {+25, −25, +50, −50} bp applied to every real level value at every bar: L′_t = L_t·(1 + o × 10⁻⁴). The same arming, event, feature and label rules apply. A placebo event is dropped if any real level (any type, any box) lies within 10 bp of L′_t at t.
- **Secondary placebos:** offsets of ±0.5σ_b(t) and ±1.0σ_b(t). These are reported, not used for pass/fail.
- Placebo events inherit **no** lean. They are used only in the H2 interaction.

## 10. Statistics, pass and fail

All statistics are computed on `CLOCK_OK` events only, separately per split. Confidence intervals use a block bootstrap by UTC calendar day: resample days with replacement within the split, recompute every statistic on the same resampled days for real and placebo events, B = 2,000, seed 20261003, percentile intervals.

| ID | Statistic | **PASS** (all conditions) | **FAIL** |
|---|---|---|---|
| **S1-H1** | Per primary cell: p̂_c, exact two-sided binomial test of n_R against 0.5, Benjamini–Hochberg across all populated primary cells | At least one cell with: develop BH q < 0.10, \|p̂_c − 0.5\| ≥ 0.05 and n_R + n_B ≥ 100; validate on the same side of 0.5 with a one-sided binomial p < 0.05 and n ≥ 30; test on the same side (point estimate) with n ≥ 15 | Otherwise |
| **S1-H2** | For H ∈ {RESPECT, BREAK}: Δ_real(H) = mean Y_fwd^H(3) given `confirm_H` minus mean given not `confirm_H`, over real events. Δ_plac(H) is the same over pooled primary placebo events. I(H) = Δ_real(H) − Δ_plac(H) | For the same H on both validate and test: the lower bound of the 97.5% interval for I(H) is > 0 (Bonferroni over the two H), **and** Δ_real(H) > 0 | Otherwise |
| **S1-G** | AGREE events: mean Y_net(3) at the branch's primary fee, and the same quantity for lean-cell `FLAT_WATCH` events for comparison | S1-H1 passes; n_AGREE ≥ 30 on validate and ≥ 15 on test; validate mean > 0 with a 95% lower bound > 0; test mean > 0; no calendar month and no UTC hour supplies more than 50% of Σ Y_net(3) over AGREE events | Otherwise |
| Power (always reported) | Events per cell; minimum detectable I(H) ≈ 2.8 × bootstrap SE | n/a | n/a |

### Decision table

| H1 | H2 | G | Next action |
|---|---|---|---|
| Pass | Pass | Pass | Proceed to S2 (1 s tape), S2b and S3 design. The lean cells and confirm rules become S2's baseline |
| Pass | Fail | any | The level leans but bar flow adds nothing at 1 m. S2 must show the interaction at 1 s before any DOM work is justified |
| Fail | Pass | n/a | Flow is level-specific but no level leans. Under the locked `INDEPENDENT_AGREE` the gate cannot fire. Escalate to Desk Floor (program, Appendix C item 5). Do not let the burst choose the direction |
| Fail | Fail | n/a | Run P1 placebo diagnostics and S2. Hold DOM-study investment until S2 reports |
| Pass | Pass | Fail | Information exists but does not clear fees at 3 m. Check the 5, 15 and 30 m horizons as diagnostics (not a pass route), and check the maker-only share in S2 |

## 11. Robustness runs (reported; never used to pass or fail)

`TI_into` threshold 0.10 and 0.30; arming 10 and 20 bars; r = 5 and 20 bp; H = 15 and 60 bars; `CAL=PROXY`; clusters excluded; `BOX=EXCLUSIVE`; UTC box only; NY box only; σ placebos; a 5 m-bar version (arming 3 bars, H = 6 bars) for comparison with `[BAYES-0102]`, which used 5 m bars.

Added in v1.1 from [Iteration 01](20261003-iter01-gate-after-1002-stills.md):

| Row | Definition |
|---|---|
| R-OI | Split `confirm_RESPECT` events by `oi_d5c` > 0 against ≤ 0 ("loaded" against plain absorption). Report Δ_real(RESPECT) and the mean Y_net(3) of AGREE events per split |
| R-REGIME | Set `regime_tag` from the open time of bar t: `post_cash` for 16:00–16:59 America/New_York, `cme_break` for 17:00–17:59, `other` otherwise. Report every H2 and G statistic for UTC-box events per `regime_tag` |
| R-STOP | In the AGREE replay, add a stop at a placeholder 10 bp from L on the losing side: P_stop = L·(1 − s·0.001) for RESPECT and L·(1 + s·0.001) for BREAK. Let j be the first bar in t+1..t+3 that touches the stop (Lo_j ≤ P_stop when dir = +1; Hi_j ≥ P_stop when dir = −1). The exit is min(O_j, P_stop) for dir = +1 and max(O_j, P_stop) for dir = −1, so a bar that opens beyond the stop fills at its open. If no bar touches, the exit is C_{t+3}. A stopped exit is a taker exit, so the fee becomes 1.09 bp for RESPECT and 2.18 bp for BREAK. Report Y_net(3) with and without the stop, and the stop-out rate |

## 12. Outputs

Raw data is not committed. Outputs go under `desk-briefs/hft-strategies/aggression-bayes/results/s1_v<version>/` (for this version, `results/s1_v1.1/`):

| File | Content |
|---|---|
| `inputs_manifest.csv` | Every input file: URL, sha256, rows, date |
| `s0_reconciliation.csv` | The §2.2 known answers, recomputed |
| `events.parquet` (not committed if large; summary committed) | One row per real or placebo event: `event_id, cluster_id, is_placebo, offset_bp, split, box, date, open_time, level_type, instance_id, L, s, tsib_bucket, speed15, dist_vwap_sigma, ib_width_rel, vwap_slope30, touch_seq, TI_t, TI_into, pen_t, pen_class, cl_t, vz_t, atsz_t, oi_d5c, oi_na, TI_spot_t, Y_level, Y_fwd_3, Y_fwd_5, Y_fwd_15, Y_fwd_30, clock_ok, impulse, cal_tag, algebra_tag, regime_tag` (from v1.1; `Y_stop_3` and `stopped` in the AGREE replay) |
| `h1_cells.csv` | Per primary cell and split: n_R, n_B, n_NONE, p̂, binomial p, BH q, pass flag |
| `h2_interaction.csv` | Per H and split: Δ_real, Δ_plac, I, CI, n |
| `gate_log.parquet` and `gate_summary.csv` | Per event: each flag, first failing flag, AGREE flag, Y_net at 0 / 1.09 / 2.18 |
| `volume_shadow.csv` | Per split: `episodes`, `V_fake_shadow` by excluded category (ungated touch-and-follow, 1u per event) |
| `YYYYMMDD-s1-results.md` | The write-up, opening with the decision-table row reached |

## 13. Tests that must pass before results are read

| Test | Assertion |
|---|---|
| T1 Prefix invariance | Truncating the data after day D leaves every feature and gate flag of events on or before D (whose labels are complete) unchanged |
| T2 VWAP | Resets at each box anchor; equals a hand calculation on a 3-bar toy box; uses bars ≤ t−1 only |
| T3 DST | NY anchor = 14:30 UTC on 2026-03-06, 13:30 UTC on 2026-03-09, 13:30 UTC on 2025-10-31, 14:30 UTC on 2025-11-03 |
| T4 Windows | No event before A + 75 m or at or after End − 30 m; no NY box on the listed holidays |
| T5 Labels | `Y_fwd` reads only bars ≥ t+1; `Y_level` reads only bars ≥ t |
| T6 Formats | Spot µs timestamps are converted (`open_time // 1000`); perp header rows are skipped; metrics are sorted, with 288 stamps a day expected and gaps flagged |
| T7 Checksums | Every file's sha256 matches its `.CHECKSUM` |
| T8 S0 | The §2.2 known answers are reproduced exactly |
| T9 Placebo hygiene | No placebo event within 10 bp of a real level |
| T10 Determinism | Two runs with seed 20261003 give identical outputs |

## 14. What S1 cannot say

- **Missing evidence.** S1 has no DOM, so `DEPTH_AGREE`, quote-walk and spoof detection are not testable. It has no true mid, so the 180 s markout is a 3-minute close-to-open proxy carrying bid-ask bounce.
- **Coarse resolution.** OI is 5-minute, so `LIQ_VETO` is coarse. A 1-minute "burst" is a blunt stand-in for a 15-second burst.
- **Scope of a pass.** A pass means the idea survives at bar resolution and the finer studies are worth funding. It does not mean the strategy works.
- **Scope of a fail.** A fail at 1 m does not rule out an effect at 1 s; S2 decides that.
