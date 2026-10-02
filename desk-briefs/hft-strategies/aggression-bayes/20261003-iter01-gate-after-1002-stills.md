# Iteration 01: what I would change in the joint gate after the 2 Oct stills

**PAPER ONLY.** These are proposals to Desk Floor. The five flag names and their order are unchanged. One session is an anecdote, so every change below is a hypothesis paired with the study that tests it, not a rule adopted on the strength of two screenshots.

Tags as in the parent program: `[still]` means read off the two desk stills; `[PR7]` means taken from [PR #7](https://github.com/Czegledi92/mm-regime-logger/pull/7) and not re-verified by this run.

Parent: [`20261003-level-x-live-flow-program.md`](20261003-level-x-live-flow-program.md). Study 1 spec: [`20261003-s1-level-x-bar-flow-spec.md`](20261003-s1-level-x-bar-flow-spec.md).

## The lesson in one sentence

A bid that is displayed, and even hit once without giving way, is not proof of defence. At 16:30 ET it was the liquidity a seller waited eleven minutes to use at 16:41. A gate that reads 16:30 as "branch B confirmed" is reading the invitation, not the outcome.

## What the stills and the tape read show

| Time (ET) | Fact |
|---|---|
| 16:30 | Bar O 84,310.20 / H 84,332.40 / L 84,300.00 / C 84,332.40, +22.20 on 379.67 BTC `[still]`. Order-book depth delta (0–5%) **94.86M**. Yellow heatmap bands around 84,300–84,360. Footprint is two-sided: 223.57 / 215.05 at 84,310 and 147.20 / 143.89 at 84,300. "UNFINISHED AUCTION" label `[still]` |
| 16:30 | Net taker flow −58.6 BTC while the bar closed up; OI +159.6 BTC `[PR7]` |
| 16:31–16:40 | Coil drifting up to 84,391 on 20–70 BTC a minute; OI +123 `[PR7]` |
| 16:41 | 1,536.8 BTC, 94.7% taker sell, net −1,372.4 BTC, low 84,249.8; OI +967.3; long liquidations 0.30 BTC `[PR7]` |
| 16:43 | Session low **84,188.80** `[still]` |
| After the candle | Depth panel lower: right-edge tag **30.39M** `[still]`. When during the minute the cushion fell is **unknown** |
| 17:25 → 17:26 | The same sequence at smaller scale. Depth delta **40.31M** with a one-tick bar of 48.65 BTC `[still]`, 95% taker sell `[PR7]`. Then 17:26: about 358 BTC sold against 24 bought, OI +67 `[PR7]` |

## How the current gate would have behaved (hypothetical level)

No frozen session VWAP or IB level is visible near 84,300 on the stills (Appendix A of the parent), so in reality the gate stands down. To test the gate's logic, suppose a primary level had been frozen at about 84,300 with a RESPECT lean.

| Time (ET) | Current spec | Problem |
|---|---|---|
| 16:30 | `PRINT_CONFIRM` passes (prints at the level). Absorption confirms RESPECT. `DEPTH_AGREE` B passes (large displayed bid, two-sided book). Result: **B AGREE**; maker quotes rest around the level, and the instance is spent | Displayed size and one absorbed minute are treated as defence |
| 16:31–16:40 | B round trips in the coil | Fine while it lasts |
| 16:41 | The level breaks against B. S1 v1.0 has no stop: its replay holds a fixed 3 bars and exits at C_{t+3}, so it books the whole adverse move and cannot say where a stopped B position would have got out inside a 141-point minute | No stop, and the only exit clock is the minute close |
| 16:41 (A side) | `EPISODE_ONCE` has already spent the instance on B, so the continuation sweep cannot be an A trade | Correct by design (no flipping), but the cost is invisible |
| 17:25 → 17:26 | The same pattern, smaller. Both sweeps pass `LIQ_VETO` because OI did not fall | `LIQ_VETO` cannot tell a committed sweep (16:41) from a weak one (17:26) |

## Proposed changes, ranked

| # | Change | Flag (owner) | What in the stills motivated it | Test, and when | Status |
|---|---|---|---|---|---|
| **C1** | **`DEPTH_AGREE` B becomes a hold condition, and only "tested" depth counts.** Re-evaluate every second during a B episode. The defended side's depth within k bp must stay at or above ρ_hold × its value at entry, or B exits. At entry, displayed size counts only after it has been hit and refilled (refill ratio ≥ ρ); untested display is neutral | `DEPTH_AGREE` (MMT) | 94.86M displayed at 16:30, 30.39M at the right edge after the consumption; 40.31M at 17:25 before the 17:26 sweep `[still]` | Coarse and public now: S2b, using whether the ±1% bid cushion in `bookDepth` falls in the 30–300 s before sweeps through levels. Properly: S3 with Richard's DOM | Proposal; design input for S2b and S3 |
| **C2** | **Absorption while the aggressor side is opening (OI up) is "loaded absorption": neutral for RESPECT, not a confirm.** Absorption with OI flat or down still confirms. This mirrors `LIQ_VETO` | `INDEPENDENT_AGREE` burst classification (Lucas) | At 16:30, price closed up on net taker selling while OI rose 159.6 BTC `[PR7]`. The sellers were at least partly opening, so their inventory stayed in the market waiting for the bid to fail | **Free in S1 now** as a robustness split of `confirm_RESPECT` by the sign of `oi_d5c` (spec §11, row R-OI). Properly in S3 with polled OI | Proposal; S1 robustness row added |
| **C3** | **Use an OI conviction ratio for branch A scale-ins.** `oi_conv` = oi_Δ / \|Σ signed qty\| over the burst. The binary `LIQ_VETO` stays as is for first entries; adds also require `oi_conv` ≥ c (placeholder 0.5) | `INDEPENDENT_AGREE` (Lucas); state machine | From the `[PR7]` figures: 16:41 ≈ 967.3 / 1,372.4 ≈ 0.70; 17:26 ≈ 67 / 333.9 ≈ 0.20. 16:41 travelled about 141 points and the OI stuck; 17:26 travelled about 58 points and was repaired `[PR7]`. Both pass `LIQ_VETO` | S3 with OI polled every 5 s or faster. S1 and S2 can only do a noisy 5 m version | Proposal |
| **C4** | **`PRINT_CONFIRM` returns a typed signature instead of pass/fail:** `SWEEP_THROUGH` (A evidence), `ONE_SIDED_INTO_HELD` (B evidence), `TWO_SIDED_NODE` (neutral on its own), `NONE` | `PRINT_CONFIRM` (QA) | The heavy prints at 84,300–84,310 at 16:30 were two-sided (223.57 vs 215.05) `[still]`. Under "prints at the level" they would pass for either branch | S2: per-second buy and sell volume at the level from `trades`. S3 | Proposal |
| **C5** | **Stops and B exits run on the 1 s clock.** S1 v1.0 has only a fixed 3-bar exit. R-STOP adds a stop with an intrabar fill rule: the stop price if a bar's range touches it, or the bar's open if the bar gaps through | State machine; `EDGE_OK` side-being-run (Benjamin, MMT) | 16:41 moved about 141 points inside one minute `[PR7]`. A minute-close exit cannot represent a B exit inside that move | S1 robustness row R-STOP (intrabar stop fill); S2 and S4 use 1 s bars from `trades` | Proposal; S1 robustness row added |
| **C6** | **Make the cost of `EPISODE_ONCE` visible.** After a B episode exits at its stop, log the A-direction markout that the spent instance forfeits, as `forfeit_markout_180s`, and report `V_forfeit`. **Keep the rule strict**: flipping from B to A on the same instance generates whipsaw | `INDEPENDENT_AGREE` (Lucas); S4 metric | The 16:41 sweep is exactly the move a spent B instance cannot take | S4 | Proposal; a measurement, not a rule change |
| **C7** | **Tag the post-cash clock regimes** `post_cash` (16:00–17:00 ET, CME still open) and `cme_break` (17:00–18:00 ET, perp only), and stratify S1 by them before deciding whether `CLOCK_OK` should exclude either | `CLOCK_OK` (Macro) | 16:41 sits before the CME Friday halt and 17:26 after it; `[PR7]` reads them as different liquidity regimes. Both are outside the NY box, with only the UTC box active | **Free in S1 now** as robustness row R-REGIME | Proposal; S1 robustness row added |

## What I would not change

| Keep | Why |
|---|---|
| The level set (session VWAP and finished IB only) | The 16:41 action happened at a DOM band and the 17:26 action next to the weekly open (84,433.00 `[still]`). A level-anchored gate should stand down there unless S6 says otherwise. Promoting a level type on one session is curve-fitting |
| The `LIQ_VETO` definition | It behaved as intended on both sweeps: OI did not fall on either `[PR7]`. C3 adds graded information for adds; it does not redefine the veto |
| `EPISODE_ONCE` strictness | C6 makes its cost visible. Whether to pay that cost is a Desk Floor decision on evidence, not a reaction to one minute |
| Flag names and order | Locked |

## What the stills cannot settle

- **Timing of the cushion drop.** Whether the depth cushion fell *before* 16:41 (C1 would then have exited B early) or only *with* it (C1 would not have helped) needs sub-minute book data.
- **Pulled vs filled size.** Whether any of the 16:30 displayed bid was pulled rather than filled (`SPOOF_PULL_VETO`) cannot be seen; cancels are invisible on the stills, as `[PR7]` also says.
- **Who was on the passive side.** That is not identifiable from public data.

## Asks to Desk Floor

1. **Approve C2 and C7 as Study 1 robustness strata now.** They cost nothing and need no new data.
2. **Accept C1, C3 and C4 as design inputs** for S2b and S3. They become rules only if those studies pass.
3. **Accept C5 and C6 as simulation conventions** for S1 and S4.

## Changes made to the Study 1 spec in this iteration

The spec moves to v1.1. Its §11 robustness list gains three rows, and §12 gains a `regime_tag` column. None of this is used for pass or fail, so the primary S1 result cannot change. The exact definitions live in the spec; this is the summary.

| Row | From | What it reports |
|---|---|---|
| R-OI | C2 | `confirm_RESPECT` split by the sign of `oi_d5c`: is "loaded" absorption weaker than plain absorption? |
| R-REGIME | C7 | H2 and G statistics for UTC-box events in `post_cash` (16:00–16:59 ET), `cme_break` (17:00–17:59 ET) and `other` |
| R-STOP | C5 | Y_net(3) of AGREE events with an intrabar stop placed 10 bp beyond L on the losing side (placeholder), filled at the stop or at a gapping bar's open, with taker fees on stopped exits; plus the stop-out rate |
