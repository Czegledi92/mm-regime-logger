# Tape read: BTCUSDT "3 stepped asks tracking VWAP?" (paper only)

- Date: 2026-10-06
- Author: Opus 5.5 cloud agent (produced independently; no GPT-model output was consulted)
- Scope: paper research only. **No live orders.** Nothing here is a trade instruction.
- Source: Richard's Binance BTCUSDT 10m chart screenshot, filed next to this brief as
  [`20261006-vwap-tracking-asks.png`](./20261006-vwap-tracking-asks.png).

> **Artifact status: the PNG is missing.** The chart attachment was never written to the agent's
> disk: the expected path did not exist, and a filesystem search found no copy. So the PNG is
> **not committed**, and the link above is a placeholder until someone adds the file. It also
> means **no pixels were measured in code**. Every AXIS-ESTIMATED number below comes from
> reading pixel coordinates by eye on the image as displayed (about 1024 x 1014 px), followed by
> a scripted linear fit. When the PNG is added, re-run the measurement with the method in
> section 1.1 and replace these estimates.

## Labels used

| Label | Meaning |
|---|---|
| **READ** | Printed on the chart (axis label, price tag, ladder cell, date label). Copied as shown. |
| **AXIS-ESTIMATED** | Computed from the pixel position using the calibration in section 1.1. Each one carries a ± error. |
| **UNREAD** | Not printed and not derivable. A best inference may be given, but it is marked as one. |
| **INFERRED** | A reasoning step built on READ or AXIS-ESTIMATED inputs. It is not a measurement. |

---

## 1. Identifying the asks

### 1.1 Pixel-to-price and pixel-to-time method

**Price axis.** I fitted price = a + b * y (y is the image row, from the top) by least squares to
7 printed tags. Their y-positions were read by eye.

| Printed tag (READ) | y (px, by eye) | Fit | Residual $ |
|---|---|---|---|
| High 86728.52 | 223 | 86726.7 | +1.8 |
| Prev Day Low 84972.01 | 530 | 84974.1 | -2.1 |
| Weekly Open 86530.00 | 258 | 86526.9 | +3.1 |
| Prev Day High 86999.11 | 175 | 87000.8 | -1.6 |
| Prev Week High 87220.00 | 136 | 87223.4 | -3.4 |
| Daily Open 85766.87 | 391 | 85767.6 | -0.8 |
| Crosshair price 86193.06 | 317 | 86190.1 | +3.0 |

- Fit: b = **-5.709 $/px**, a = 87999.8. Calibration residuals are within ±$3.4.
- Per-line error. Reading a 1 px yellow line by eye is good to about ±3 px, which is ±$17. Adding
  the calibration residual gives **±$20 for ask lines**. The red/green moving line is thicker and
  curved, so it is good to about ±5 px, or **±$30**.
- Independent check: the crosshair sits on the lowest left-arrow line, and the chart prints
  86193.06 for it (READ). The order-book ladder pop-up highlights the **86190** row in yellow
  (READ). The fit gives 86190 for the same pixel row.

**Time axis.** The printed time labels are 08:00 at x of about 229 and the crosshair label
"Mon, 05 Oct 2026 17:50" at x of about 446. That gives **22.07 px/h, or about 3.7 px per 10m bar**.
The 02:00 label at x of about 627 lands on Oct 6 02:00 under this fit, which checks out.
Error: ±5 px, or **about ±15 min**. The chart's **time zone is UNREAD**. The chart prints
"15h 4m ago" for 17:50, so the screenshot was taken around 08:54 Oct 6 in chart time. That is
about 4 h before this ask's 12:57 UTC timestamp, so either the chart is not in UTC or the
screenshot is older than the ask. Treat this as unresolved.

### 1.2 Yellow line sets

The yellow lines carry no price or size labels (UNREAD on the lines themselves). The yellow
ladder highlight suggests yellow marks large resting size (INFERRED).

| Set | Location | Time span (AXIS-EST, ±15 min) | Line prices (AXIS-EST, ±$20) | Spacing |
|---|---|---|---|---|
| Pre-0 (candidate) | short dashes over the ~10:05 spike | about 10:20 Oct 5, a few bars | 87286 / 87241 / 87201 | uneven (45 / 40) |
| Pre-1 (candidate) | short dashes just right of the spike | about 10:20 to 11:40 Oct 5 | 86807 / 86767 / 86698 | uneven (40 / 69) |
| **A (left arrow)** | three parallel lines, x 310 to 445 | **about 11:40 to 17:47 Oct 5** | **86384 / 86287 / 86190** | **$97 / $97 (about 11.2 bps)** |
| **B (right arrow)** | three parallel lines from x 448 | **about 17:55 Oct 5** to about 05:20 Oct 6 (lowest line) and about 08:00 to 08:45 Oct 6 (upper two) | **86595 / 86527 / 86458** | **$69 / $69 (about 7.9 bps)** |
| Separate level (not part of a 3-set) | one long line from x 316 | about 11:40 Oct 5 to about 08:00 Oct 6 | 86664 | n/a |

- **First appearance of a clean, evenly spaced triple: Set A at about 11:40 Oct 5** (AXIS-EST).
  Pre-0 and Pre-1 may be earlier steps. Their spacing is uneven, so I don't count them as the
  same order set.
- **Step A to B at about 17:47 to 17:55 Oct 5** (AXIS-EST), matched rank by rank:
  - lowest line +$268
  - middle line +$240
  - top line +$211

  This is about +$240 on average, and the **set moved up**.
- **Sizes:**
  - **86190 line: about 100 (READ).** The ladder row 86190 shows 100.05 / 100.48 / 0.13. The
    units are UNREAD; BTC is likely, which at about $86.2k is about $8.6M per level (INFERRED).
  - The other two Set A lines (86287, 86384) are outside the ladder window: **UNREAD**.
  - All Set B sizes: **UNREAD**. The right-axis numbers 149.36 (at about 86600) and 132.32 (at
    about 86660) are READ, but their bucket width and units are UNREAD, so I can't attribute
    them to single orders.
  - **"Identical size" is therefore unverified.** Only one of the six levels has a readable size.
- **Ladder columns (READ values, UNREAD meaning):**
  - 86210: 7.00 / 6.98 / 0.04
  - 86205: 1.04 / 2.84 / 2.45
  - 86200: 1.27 / 1.38 / 1.36
  - 86195: 0.06 / **0.02** (boxed) / 3.50
  - 86190: **100.05 / 100.48** (yellow) / 0.13
  - 86185: 0.13 / 0.01 / 0.04
  - 86180: 4.05 / 4.05 / 4.05

  If the three columns are consecutive time slices (INFERRED, not confirmed), 86190 drops from
  about 100 to 0.13 in the third column. That is consistent with the A-to-B step happening at
  about 17:50.
- **Spacing is not the same between sets.** Set A is spaced $97 apart and Set B $69. So either
  the spacing rule is not fixed in $ or in bps (11.2 vs 7.9 bps), or the heatmap draws levels in
  price buckets. The right-axis numbers sit about 12 px (about $70) apart, which is the same as
  Set B's spacing, so bucket rendering could be producing it. This is a flagged rendering risk.

### 1.3 The tracked line

- **Identity: UNREAD.** The indicator legend is collapsed ("4 indicators", READ).
  - Best inference: a session VWAP, or an EMA with a ribbon, drawn red when price is below it
    and green when above.
  - It could also be an anchored VWAP or a plain moving average. Nothing printed separates these.
- **Current value:**
  - **85796.72 (READ number)** on the red right-axis tag at the line's endpoint. The fit puts the
    line end at about 85802.
  - Attributing that tag to this line is **INFERRED**. It could belong to another of the 4
    indicators.
- **Historical values (AXIS-EST, ±$30):**
  - about 86150 at Set A's start (11:40)
  - about 86002 at the A-to-B step (17:50)
  - about 85631 near the Oct 6 low (about 02:10)

### 1.4 Other printed context (READ)

- Last price: 86274.64 (teal tag).
- Visible-range High: 86728.52.
- Levels: Prev Week High 87220.00, Prev Day High 86999.11, Weekly Open 86530.00, Daily Open
  85766.87, Prev Day Low 84972.01.
- Lower panels:
  - "binance -2.2K": an orange cumulative line, falling all session. The indicator type is
    UNREAD; it is probably CVD.
  - "b 3.80": a delta histogram.
  - -32.54M: a bottom oscillator. Its type is UNREAD.
- Spot or perp: **UNREAD**. The header shows only "BTCUSDT Bitcoin" with a Binance icon.

---

## 2. Quoting distance (ask minus tracked line)

The ask prices and line values are AXIS-ESTIMATED (asks ±$20, line ±$30, so each difference is
about ±$36 combined in quadrature). The one exception is the "now" row, where the line value is
READ (85796.72) and only the asks are estimated (±$20). bps = (ask - line) / line * 1e4.

| Step / time (AXIS-EST) | Line (label) | Low ask: $ / bps | Mid ask: $ / bps | Top ask: $ / bps | Ask spacing |
|---|---|---|---|---|---|
| A start, about 11:40 Oct 5 | 86150 (AX) | +40 / 4.6 | +137 / 15.9 | +234 / 27.2 | $97 / 11.2 bps |
| A end, about 17:47 Oct 5 (asks unchanged) | 86002 (AX) | +188 / 21.9 | +285 / 33.2 | +382 / 44.5 | $97 |
| B start, about 17:55 Oct 5 | 86002 (AX) | +457 / 53.1 | +525 / 61.1 | +594 / 69.0 | $69 / 7.9 bps |
| B near low, about 02:10 Oct 6 | 85631 (AX) | +828 / 96.7 | +896 / 104.7 | +965 / 112.7 | $69 |
| B now, about 08:45 Oct 6 | **85796.72 (READ; attribution INFERRED)** | +662 / 77.1 | +730 / 85.1 | +799 / 93.1 | $69 |

**Distance to last price** (86274.64 READ, B asks AXIS-EST ±$20):

- low ask +$184 (21.3 bps)
- mid ask +$252 (29.2 bps)
- top ask +$321 (37.2 bps)

**Distance from the 86190 level to the 17:50 candles: UNREAD.** Candle closes are not printed,
and the candles sit at about 86000 by eye.

**Verdict on the offset: neither constant in $ nor constant in bps.**

- The low-ask gap to the line went 4.6, then 21.9, then 53.1, then 96.7, then 77.1 bps.
- Set A sat still for about 6 h while the line fell about $150, so its offset widened.
- At the only visible re-quote, the set **stepped up about $240 while the line was flat to
  falling**. That is the opposite of pegging to the line.
- The best description is **band-like and loose**, roughly 20 to 110 bps above the line. A
  rule anchored to last price or mid fits at least as well as one anchored to the line. Set B's
  low ask is about 21 bps above last at the current print (INFERRED; the price-anchor
  alternative needs testing with real data).

---

## 3. Why would a desk do this? Ranked explanations

The ranking uses only what the chart shows:

- The size is large and displayed (about 100 on one level).
- The orders rest well above the market, from tens to over 100 bps above the line.
- One set stayed still for about 6 h and then stepped up, away from price.
- The chart shows no fills.

| Rank | Hypothesis | Fit to chart | Confirms | Refutes |
|---|---|---|---|---|
| 1 | **MM inventory skew or passive offload**: a long holder or MM rests asks a set distance above mid or last and re-anchors as price moves | Good. Big displayed size, far from touch, steps when price nears the lowest level | Partial fills at the lowest level when price trades into it. The desk's bid side thins at the same time (skew). Each re-quote keys on mid/last moves, not the line. Size is refreshed after fills | No fills ever, even when price trades through. Equal re-quote timing whatever price does. Bids grow alongside the asks (neutral MM) |
| 2 | **Liquidity wall capping price**. *Spoofing or layering is only a flagged hypothesis, not a finding.* | Plausible. Large, even ladder of asks; moved away on approach | Price stalls or reverses below the wall. **Flagged pattern:** cancels or re-places when price comes within about X bps, near-zero fill ratio, re-placement timed to aggressive opposite-side flow | Real fills when touched. The wall still rests when price reaches it. Displayed size gets eaten and refreshed rather than pulled |
| 3 | **VWAP-pegged sell or execution algo** working above the benchmark (Richard's read) | Weak on this chart. The offset widened as the line fell, and the step went up while the line was flat or down. The line's identity is UNREAD, so a different VWAP (anchored or rolling) can't be ruled out | Re-quotes line up in time with changes in the true VWAP. The offset stays constant in $ or bps against a VWAP rebuilt from trades. Fills cluster when price is above VWAP. Steps follow the VWAP slope in sign | Re-quotes are uncorrelated with the VWAP rebuilt from trades. Steps run against the VWAP slope (as seen here) |
| 4 | **Passive iceberg or TWAP slicing** | Weak. Icebergs show small display and refill; this shows about 100 displayed. TWAP children usually sit at or near the touch and fill | Small displayed clips that refresh at the same price after each trade. Fills at fixed intervals. Hidden-size signature (trade volume at the level larger than the visible size) | Large static display that never trades |
| 5 | **Options delta or basis hedge** (asks near strikes or round numbers) | Weak. The levels (86190, 86287, 86384 / 86458, 86527, 86595) are not round strikes | Levels sit at or near listed strikes. Re-quotes follow moves in implied delta or the expiry calendar. The opposite side shows up on Deribit, OKX or CME at the same time | Levels don't relate to strikes. No link to options flow |
| 6 | **Funding or basis desk** (spot-perp carry) | Weakest. Carry trades rarely leave displayed ladders far from touch | Asks pair with perp bids, or the reverse. Re-quotes follow funding prints or 8h boundaries. Size matches the basis notional | No link to funding times or the perp book |

---

## 4. Paper measurement plan (Binance book + trades from Tardis in the desk DB)

**Data.**

- Tardis `book_snapshot_*`, or `incremental_book_L2` (depth diffs) seeded by a snapshot, plus
  `trades` for BINANCE spot BTCUSDT.
- Run it on USDⓈ-M as well, because spot vs perp is UNREAD.
- Window: Oct 5 00:00 to Oct 6 12:00. Pad by ±2 h because the time zone is UNREAD.
- **Coverage is unaudited.** First count gaps:
  - missing update IDs, and points where `first_update_id` is not `prev_last + 1`
  - snapshot resyncs
  - timestamp jumps over 1 s

  Then mark any step that falls in a gap as UNMEASURED.

**Step 1: rebuild the book.** Apply the depth diffs to an in-memory L2 book. Each update gives a
per-level (price, qty, ts) time series for asks within 200 bps of mid.

**Step 2: detect a same-size order set.** L2 is aggregated per level, so single orders can't be
seen directly. Proxy:

- Find add events: one update where a level's qty rises by Δq, with Δq at or above a threshold
  set from the distribution (for example the 99.9th percentile of level deltas).
- Group adds that fall within the same 1 to 2 s window and whose Δq values are within 1% of each
  other.
- Accept a group as a set when it has 3 or more levels, roughly even price spacing, and the same
  Δq. Call this set S_k.
- Linking: a set "re-quotes" when, within Δt, about the same Δq leaves the old levels and about
  the same Δq arrives at 3 new evenly spaced levels.
- Record:
  - the step time
  - the old and new prices
  - spacing in $ and bps
  - mid and last at the step
  - the time since the last trade at the old levels

**Step 3: rebuild the benchmark.** Compute these from `trades` rather than trusting the chart's
line:

- session VWAP (UTC 00:00 anchor)
- rolling VWAP over 1h, 4h and 24h
- anchored VWAP from the spike at about 10:05
- EMA 20 and 50 on 10m closes

For each candidate, regress the re-quote offset (ask - benchmark) on time. The best-tracked
benchmark is the one with the smallest offset variance and step signs that match its slope. If
no candidate beats "anchored to mid/last", reject the VWAP-peg hypothesis.

**Step 4: fills vs pulls.** For each level and interval, compare the qty decrease Δq⁻ with the
buyer-initiated trade volume printed at that price, V_trade.

- consumed = min(Δq⁻, V_trade)
- pulled = Δq⁻ - consumed
- fill rate = Σ consumed / Σ displayed qty (time-weighted), per set and per step
- Also log:
  - how the set behaves as mid comes within 5, 10 or 20 bps (hold, pull or step)
  - whether size refreshes after a partial fill
  - pull latency after an aggressive buy burst

**Step 5: outputs.**

- a per-step table matching section 2, filled from data
- the fill rate with a binomial CI
- the pull-on-approach rate
- a benchmark-fit ranking
- a coverage report

If the pull-on-approach rate is high and the fill rate is near zero, flag hypothesis 2 (spoofing
or layering). Don't conclude it from this alone.

### 4.1 Paper trade-around idea (scored only by EV at 1R after costs)

**Two versions:**

- **Fade under the wall (if hypothesis 1 or 2 holds).** Paper-short at the touch when mid comes
  within D bps under the lowest ask of a confirmed set. Stop 1R above the lowest ask. Target 1R.
- **Break or pull long.** If the set pulls or gets filled through, paper-long on the first trade
  above the old lowest ask. Stop and target at 1R.

**Costs (taker both sides):**

- Base: Bitunix VIP8 taker 0.026% per fill = 2.6 bps, times 2 = 5.2 bps, plus slippage of
  1.48 bps entry and 0.39 bps exit. **C = 7.07 bps round trip.**
- 60% rebate case: 2.6 * 0.4 * 2 = 2.08 bps, plus 1.87 bps slippage. **C = 3.95 bps.**

**Score.**

EV per trade = (2p - 1) * R - C, in bps. Breakeven: **p\* = 0.5 + C / (2R)**.

| R (bps), a sweep only, not a recommendation | p\* at C = 7.07 | p\* at C = 3.95 |
|---|---|---|
| 10 | 0.854 | 0.698 |
| 20 | 0.677 | 0.599 |
| 40 | 0.588 | 0.549 |
| 80 | 0.544 | 0.525 |

- The hit rate p is **UNMEASURED**. It must come from the step 4 backtest.
- Don't score EV until p has a CI from at least N events. N is UNSET.
- At small R, costs dominate. The idea only makes sense if R is several times C.
- **UNSET:** notional, latency budget, EV floor, D, R.

---

## 5. Biggest unknowns

1. The PNG was not available to the agent, so every AXIS-ESTIMATED number is a by-eye pixel read
   (±$20 for asks, ±$30 for the line). Re-measure once the file is added.
2. The tracked line's identity is UNREAD. Attributing 85796.72 to it is INFERRED.
3. Sizes are READ for only one level (86190, about 100, units UNREAD). "Identical size" is
   unverified.
4. Heatmap bucket rendering may be creating the Set B spacing.
5. Time zone, spot vs perp, and the meaning of the ladder columns are all UNREAD.
6. The chart shows no fill or pull evidence. Tardis coverage is unaudited.
