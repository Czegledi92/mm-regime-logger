# Order Book Pressure (OpenMarket library) — indicator catalog note

**Catalog entry · kScript (`//@version=2`, modern engine) · onchart overlay · author: openmarket**

| | |
|---|---|
| Status | **PAPER / reference only.** Describes what the script computes and draws. No strategy, no orders, no backtest, no sizing, no notional. |
| Read | Independent pass B. Not coordinated with or merged from any sibling pass. |
| Inputs | Script source pasted by the desk (truncated inside the band-4 plot block); the desk's paraphrase of the truncated color/plot section; three library screenshots: "What it shows" + worked example, "When it fails" + "Settings that matter", and the short DESCRIPTION. |
| Docs checked | OpenMarket kScript reference, fetched by this pass 2026-10-04 ~23:00 UTC (the desk's own fetch is dated 2026-10-05). URLs in §8. |
| Not available | Running the script. No chart, no book data, no live output was observed. Every statement below comes from the code text or the docs. |

Evidence tags:

- **[CODE]** read directly from the pasted source lines.
- **[PARA]** from the desk's paraphrase of the plot section, which was not pasted. It is consistent with the code but not verified against it.
- **[DOC]** stated in a cited OpenMarket kScript doc page (§8).
- **[LIB]** stated in the library screenshots.
- **[I]** this pass's interpretation.

---

## Bottom line

1. **Dialect: kScript, modern engine.** The `//@version=2` header and the current `//@version=3` template run on the same engine. OpenMarket's v2-vs-v3 guide says the two markers are "interchangeable" and route "to the modern engine". Only a missing marker or `//@version=1` falls back to the legacy v1 engine [DOC]. Every builtin this script calls (`define`, `input`, `orderbook`, `ohlcv`, `sumBids`, `sumAsks`, `static`, `plotLine`) is in the current reference with a compatible signature (§2). So v2 and v3 are equivalent *for this script*. That is not a claim that they are the same language overall: v3 added features and corrected eight TA builtins this script does not use.
2. **What it measures.** One order-book snapshot per bar, from the chart's own symbol and venue only. On that snapshot it takes cumulative bid and ask volume within 1%, 2.5%, 5% and 10% **of the mid-price**. It cuts those into four distance slices (0–1, 1–2.5, 2.5–5, 5–10%) and computes `(bid − ask) / (bid + ask) × 100` for each slice [CODE + DOC]. Each ratio compares the bids in a slice below mid with the asks in the *mirrored* slice above mid. It is a relative number. It cannot tell "many bids" from "few asks".
3. **What is only drawn.** The reference lines (scaled by `scaleFactor`), the fill colors, the 20-step opacity ladder, the extreme-color swap, and the ±`minBidRatio` / `minAskRatio` gates change only what appears on screen. None of them changes a ratio [CODE + PARA].
4. **Settings that change the measurement: only `depth1` and `depth2`.** They decide which of the four slice ratios are computed and which are forced to 0. Some combinations switch every slice off (§4).
5. **Where the library text holds up.** The description of the ratio, the fixed depths, the scale-factor behavior, and all of "When it fails" match the code.
6. **Where it overclaims.**
   - The DESCRIPTION claims the bands show "where price is more likely to find support or resistance". The code computes no likelihood and no outcome, and the library's own "When it fails" section undercuts the claim. Refused (§6).
   - The worked example's "if price grinds into that 2.5 to 5% zone" treats a slice that moves with price as if it were a fixed price zone (§5).
   - At default settings, the worked example's +10 slice would draw no fill (§5).

---

## 1. Source as received

The pasted script runs from `//@version=2` through the `ratio4` assignment. The desk describes the color functions, color arrays, fill gate and reference-line plotting in prose, and says the paste ends inside the band-4 block. **A missing final closing brace is recorded as unconfirmed.** It may be a paste truncation. It is not treated as a bug, and nothing here proposes a fix. The indicator is documented, not rewritten.

## 2. Dialect check (kScript v2 header against the current reference)

| Item in script | What the current reference says | Status |
|---|---|---|
| `//@version=2` | "`//@version=2` and `//@version=3` are interchangeable (`=3` is canonical)". Both route to the modern engine. A missing marker or `=1` uses the legacy engine. | Same engine [DOC: v2-vs-v3, whats-new-v3] |
| `define("Order Book Pressure", "onchart", axis=false)` | Signature `define(title, position, showPriceAxis?, …)`. The reference table names the third parameter `showPriceAxis`, but every example and the engine's own error text (`define(title, position, axis)`) use `axis=`. `position` must be the literal `"onchart"`/`"offchart"`, which it is. | Accepted form; the docs disagree internally on the kwarg name [DOC: script-definition, v2-vs-v3] |
| `input(name=…, type="select", …, options=[…])` | Signature `input(name, type, defaultValue?, label, constraints?, options?, group?)`. Examples pass select options inside `constraints` as `{options: […]}`; the signature also lists `options` as its own parameter. | Matches the signature [DOC: script-definition] |
| `input("posCol", "color", "a5d6a7", "Bid Fill Color")` (positional, no `#`) | The v3.x release notes say "Legacy call forms (positional inputs, …, `static`, string colors …) all keep working". Every doc color example uses `#rrggbb`. | Positional form confirmed. **Whether a bare hex without `#` is accepted is not confirmed** by any page read |
| `input(…, type="number", constraints={min:1, max:5})` | `{min, max, step?}` constraints for `number`/`slider`. | Matches [DOC] |
| `orderbook(currentSymbol, currentExchange)` | Dedicated v2 subscription `orderbook(symbol, exchange)`, kept in v3. The source's `bids`/`asks` are "array-celled": each bar holds a list of levels. | Matches [DOC: v1-vs-v2, data sources] |
| `sumBids(ob, x)` / `sumAsks(ob, x)` | `sumBids(source, depthPct?: number = 10): number` — "total bid volume within `depthPct` of the mid-price" (asks the same). | Matches. `x` is a **percent** [DOC: orderbook-functions] |
| `static e0 = 0.0` … `static enA = …` | `static` holds values across bars; `persist` is now the preferred spelling and `static` still works. | Matches [DOC: overview, release notes] |
| `plotLine` (in the unpasted plot block) | `plotLine(value, width?, colors?, colorIndex?, fill?, …)` with a per-bar `colorIndex`. | Signature exists. **The actual calls were not pasted**, so their arguments are unverified [DOC: plotting] |

The Kiyotaka-hosted changelog (`docs.kiyotaka.ai/.../updates/changelog`) returned HTTP 500 to this pass on every attempt. This VM also has no direct egress to that host. A search-engine snippet of that page matches the text of OpenMarket's `/kscript/migrations/v1-vs-v2` page (for example, "v2 (Current) … Dedicated functions for specific data types: `ohlcv` … `orderbook(symbol, exchange)`"), so the OpenMarket copy is the version actually read. One labeling oddity: OpenMarket's release notes head the September 2025 entry "v2.0.0" and then call it a "Major release of **kScript v3**". The version numbers in the docs are not fully consistent, which is why the engine-routing statement above is the one relied on.

## 3. What is measured (from the code)

Per bar, on one snapshot `ob` [CODE]:

```
cumBid(p) = sumBids(ob, p)   cumAsk(p) = sumAsks(ob, p)   for p ∈ {1, 2.5, 5, 10}

slice A  (0–1%)    bid = cumBid(1)              ask = cumAsk(1)
slice B  (1–2.5%)  bid = cumBid(2.5) − cumBid(1)    ask = cumAsk(2.5) − cumAsk(1)
slice C  (2.5–5%)  bid = cumBid(5)   − cumBid(2.5)  ask = cumAsk(5)   − cumAsk(2.5)
slice D  (5–10%)   bid = cumBid(10)  − cumBid(5)    ask = cumAsk(10)  − cumAsk(5)

ratio_k = enabled_k ? (bid_k − ask_k) / (bid_k + ask_k) × 100 : 0      ∈ [−100, +100]
```

What the code and docs establish:

- **Anchor is mid-price, per the docs.** `sumBids`/`sumAsks` measure "within `depthPct` of the mid-price" [DOC]. The script never passes a price. It does not set the anchor itself.
- **Depths are fixed.** The `e1..e4` constants go into the sums unscaled. `scaleFactor` never touches them [CODE].
- **One venue.** `currentExchange` is the chart's own venue. The script does not aggregate across venues [CODE]. (OpenMarket's terminal order book is aggregated; this indicator is not.)
- **One snapshot per bar.** The source holds one list of levels per bar [DOC: data sources]. The strategy-tester docs likewise describe "recorded order-book snapshots (one per chart bar)" and say aggregated snapshots "cannot express queue dynamics or replenishment" [DOC: strategies/slippage]. **When within a bar the snapshot is taken is not documented** in the pages read. On a 4h chart that is one snapshot per 4h bar.
- **Units are not documented.** The reference says "volume" and does not say whether that is base or quote. The ratio uses the same unit on both sides, so it is unit-free. It is not notional-weighted, and this note computes no notional.
- **Slices are cumulative differences.** That relies on `sumBids(ob, p)` being cumulative from mid outward, which "within `depthPct` of the mid-price" supports. Whether a level exactly at a boundary counts in one slice or both is not documented.
- **No guard for an empty slice.** If an enabled slice has `bid + ask = 0`, the code divides 0 by 0. The docs advise guarding division (`denominator != 0 ? … : na`) but do not say what an unguarded 0/0 returns. The result is unconfirmed; do not assume it reads as 0.
- **No executed flow.** The only other input is `px.close`, and it is used only to place lines [CODE].

## 4. Settings: which change the measurement and which only change the drawing

| Setting (label) | Default | Effect | Measurement or drawing |
|---|---|---|---|
| `depth1` "Greater than or equal to" | `0%` | Slice k is enabled iff `d1 ≤ lower edge_k` and `upper edge_k ≤ d2`. Disabled slices are forced to `ratio = 0`. | **Measurement** (which ratios exist) [CODE] |
| `depth2` "Smaller than" | `5%` | As above. The upper edge is inclusive (`≤`), so "Smaller than 5%" *includes* the 2.5–5% slice. | **Measurement** [CODE] |
| `minBidRatio` "Ratio minimum bids" | 20 | Fill gate: a bid fill draws only if `ratio ≥ minBidRatio`. | Drawing [PARA] |
| `minAskRatio` "Ratio minimum asks" | 20 | Fill gate: an ask fill draws only if `ratio ≤ −minAskRatio`. | Drawing [PARA] |
| `scaleFactor` "Band Scale Factor (1 = Fixed Scale)" | 1, constrained 1–5 | Line at `close × (1 ± e·scaleFactor/100)`. | Drawing [CODE] |
| `showRef` "Show Reference Bands" | on | Turns the reference lines on or off. | Drawing [PARA] |
| `highlight` "Highlight Extremes?" | on | The top two of the 20 color steps use `extremecol`. | Drawing [PARA] |
| `posCol` / `negCol` / `extremecol` | `a5d6a7` / `f1627e` / `ffff00` | Colors. | Drawing [CODE] |

Window combinations that follow directly from the enable rule [CODE]:

| `depth1` → `depth2` | Slices enabled |
|---|---|
| 0% → 1% | A |
| 0% → 2.5% | A, B |
| **0% → 5% (default)** | **A, B, C** (5–10% slice off) |
| 0% → 10% | A, B, C, D |
| 1% → 5% | B, C |
| 5% → 10% | D |
| **10% → any** | **none.** Slice D needs `d1 ≤ 5`, so the "10%" option for the near edge always produces an empty indicator |
| `d1 ≥ d2` (e.g. 5% → 2.5%) | none |

Color ladder [PARA]: `|ratio|` maps in 3.5-point steps over 0–70 onto indexes 1–20, with opacity rising by index. With `highlight` on, indexes 19–20 use `extremecol`. That puts the extreme color at roughly `|ratio|` ≳ 63; the exact boundary and how values above 70 are clamped are in code that was not pasted. Fill geometry is also unconfirmed: whether a bid fill sits below price, spans the slice on both sides, or sits between the scaled lines.

## 5. Library text against the code

**Image 1, "What it shows" and the worked example**

| Library claim | Verdict |
|---|---|
| "Sums bid depth and ask depth out to fixed distances from price: 1%, 2.5%, 5% and 10%." | **Agrees**, with one qualification. The docs anchor the sums at **mid**, while the code draws lines from **bar close**. On historical bars the two can differ, and the snapshot time within the bar is undocumented. At scale 1 the lines sit at the literal percentages *from close*, which need not be exactly the measured boundary. Code + docs support "from mid" for the measurement; the screenshot's "from price" is looser. |
| Each band's ratio = (bid − ask) / total, in percent; positive = bids dominate. | **Agrees** [CODE]. "Dominate" means relative to the mirrored ask slice, not absolute size. |
| More opaque with dominance, 3.5-point steps up to 70%, top two steps extreme when highlighting is on. | **Agrees** with the paraphrase [PARA]. Not verified against pasted code. |
| With scale 1 the lines sit at the literal depths; above 1 they move out "while the liquidity itself is still measured at the fixed depths". | **Agrees** [CODE]. Above scale 1, a line no longer marks the edge of the slice it labels. |
| "Read it as a map of where size is stacked, not as a signal." | **Agrees** with the code: nothing in it is a signal. "A heavy bid slice below price" is shorthand. The ratio only says that the bid slice outweighs the mirrored ask slice. |
| Worked example: 4h chart, window 0–5%; slice A ≈ −40, B ≈ +10, C ≈ +55. | **Illustrative, as labeled.** No prices or symbol are given and none are inferred here. At default gates (20/20): A (−40) draws an ask fill; **B (+10) clears neither gate and draws no fill**; C (+55) draws a bid fill around step 16 of 20, below the extreme steps. The text says B "prints near plus 10". The pasted code shows no numeric output (no `plotText` or table), so whether the value is displayed anywhere (legend or data window) is unconfirmed. Keep both: the screenshot says the value is +10; the code supports that this slice is blank on the chart at defaults. |
| "Sellers are leaning on price in the immediate area, but the heavier bid size sits several percent lower." | **Overreads.** Resting orders are not sellers "leaning". "Heavier bid size" is relative to the ask slice at the same distance above. The ratio cannot separate a large bid stack from a thin ask slice. |
| "If price grinds into that 2.5 to 5% zone and the fill there thins as it approaches…" | **Not supported as written.** The slices are recomputed around the current mid on every bar, so price never "grinds into" a slice; the slice moves with it. Liquidity resting at a fixed price would pass from slice C into B and then A as price approaches, changing *different* ratios. Following a fixed price level needs an absolute-price view, which this indicator does not provide. |

**Image 2, "When it fails" and "Settings that matter"**

| Library claim | Verdict |
|---|---|
| Depth is not commitment; orders can be pulled. | **Agrees.** The docs also note that aggregated snapshots "cannot express queue dynamics or replenishment" [DOC]. |
| Bands are proportional to price, so boundaries move on a fast move. | **Agrees** [CODE + DOC]. |
| Ratios are relative; a thin slice can print an extreme ratio from two small orders; cross-check absolute size. | **Agrees.** The gates are ratio thresholds, not size floors, and the script has no absolute-size input [CODE]. The empty-slice 0/0 case (§3) is the limiting example. |
| Says nothing about executed trades. | **Agrees** [CODE]. |
| Near edge default 0%, options 0/1/2.5/5/10%. | **Agrees** [CODE]. **Omits** that 10% switches every slice off (§4). |
| Far edge default 5%, options 1/2.5/5/10%. | **Agrees** [CODE]. The "narrow the window for scalping decisions" guidance is usage advice the code does not support or test, and is not adopted here. |
| Ratio minimum bids/asks default 20, a floor "before a band is treated as meaningfully bid-heavy". | **Agrees** that it is a fill gate [PARA]. "Meaningfully" is a display threshold, not a statistical test. |
| Band Scale Factor default 1, range 1–5, moves lines only. | **Agrees** [CODE]. |
| Show Reference Bands on by default; off leaves the fills. | **Agrees** with the paraphrase [PARA]. Whether fill placement depends on the lines is unconfirmed (§4). |
| Highlight Extremes on by default; the top two steps use the extreme color. | **Agrees** [CODE default + PARA]. |
| Bid / ask / extreme colors. | **Agrees.** Defaults are `a5d6a7`, `f1627e`, `ffff00`, written without `#` (§2). |

**Image 3, DESCRIPTION**

| Library claim | Verdict |
|---|---|
| "Shows where buy and sell liquidity is stacked in the orderbook around the current price." | **Agrees**, for one venue and one snapshot per bar. |
| "Highlights areas where buyers or sellers are significantly stronger." | **Overclaims.** It shows resting depth, not buyer or seller strength. "Significantly" is a fixed ±20 ratio gate, not a significance test. |
| "Colored bands … at different depth levels (1%, 2.5%, 5%, 10%)." | **Agrees.** |
| "Instantly see which side of the market is heavier." | **Partly.** It shows which side is heavier *within each distance slice*, relative to the mirrored slice. No total-book comparison is drawn. |
| "Where price is more likely to find support or resistance." | **Refused** (§6). |

## 6. Refused claims

- **"More likely to find support or resistance"** (DESCRIPTION). The code computes no probability, outcome or forward return. Nothing was backtested, by OpenMarket in the material read or by this pass. The library's own "When it fails" section (pulled depth, aggressive flow through resting size) undercuts the claim. OpenMarket's orderbook-functions page says something similar ("help identify support/resistance levels"; "imbalances often precede price movements") without citing evidence. Platform docs repeating a claim do not make it supported.
- **"Sellers are leaning on price" / "a flush down has a thicker shelf to land on"** (worked example). These read intent and a conditional price path into a relative depth ratio. Not supported.
- **"Narrow the window for scalping decisions"** (settings). Usage advice; no rule or evidence in the code.
- **A trading rule, entry, exit, threshold edge, price level, symbol, or notional.** None is derived here, and none should be read from the ±20 defaults.

## 7. Open items (unconfirmed, not invented)

1. The final closing brace of the band-4 block, and the full plot section (`green_col_idx`, `red_col_idx`, the color arrays, the fill and line calls).
2. Whether a hex color without `#` is accepted.
3. The 0/0 result for an empty enabled slice.
4. When within each bar the snapshot is taken; base or quote units; how a level exactly on a boundary is counted.
5. Whether the slice ratios appear anywhere as numbers (legend or data window).

## 8. Claim ledger

**Checked against a cited doc**

| # | Claim | Source |
|---|---|---|
| C1 | The language is called kScript; the current editor template starts `//@version=3`. | https://openmarket.xyz/learn/core/k-script |
| C2 | `//@version=2` and `//@version=3` are interchangeable and route to the same modern engine; a missing marker or `=1` uses the legacy engine. | https://openmarket.xyz/kscript/migrations/v2-vs-v3 ; https://openmarket.xyz/kscript/llms-full.txt ("What's New in v3 › The version marker") |
| C3 | v2 introduced dedicated `ohlcv`/`trades`/`orderbook(symbol, exchange)` subscriptions in place of the v1 generic `source(...)`. | https://openmarket.xyz/kscript/migrations/v1-vs-v2 (the Kiyotaka copy at https://docs.kiyotaka.ai/for-developers/k-script/updates/changelog returned HTTP 500 to this pass) |
| C4 | `sumBids`/`sumAsks(source, depthPct = 10)` return total volume within `depthPct` of the **mid-price**; `depthPct` is a percent. | https://openmarket.xyz/kscript/functions/orderbook-functions |
| C5 | The `orderbook` source's `bids`/`asks` are array-celled, one list of levels per bar. | https://openmarket.xyz/kscript/llms-full.txt ("Data Sources") |
| C6 | Backtests use one order-book snapshot per chart bar, and aggregated snapshots cannot express queue dynamics or replenishment. | https://openmarket.xyz/kscript/llms-full.txt ("Slippage and Costs", `bookEstimate`) |
| C7 | `define(title, position, showPriceAxis?, …)`; `position` must be the literal `"onchart"`/`"offchart"`; examples use `axis=`. | https://openmarket.xyz/kscript/llms-full.txt ("Script Definition › define"); v2-vs-v3 page |
| C8 | `input(name, type, defaultValue?, label, constraints?, options?, group?)`; `constraints {min, max, step?}`. | https://openmarket.xyz/kscript/llms-full.txt ("Script Definition › input") |
| C9 | Positional inputs, `static`, and string colors keep working on the current engine; `persist` is the newer spelling of `static`. | https://openmarket.xyz/kscript/llms-full.txt ("Release Notes › Compatibility") |
| C10 | `plotLine(value, width?, colors?, colorIndex?, fill?, …)` exists with a per-bar `colorIndex`. | https://openmarket.xyz/kscript/llms-full.txt ("Plotting › plotLine") |
| C11 | The docs recommend guarding division by zero but do not define the unguarded result. | https://openmarket.xyz/kscript/llms-full.txt ("Division by Zero") |

**Refused or left unconfirmed**

| # | Claim | Why |
|---|---|---|
| R1 | The bands show where price is "more likely to find support or resistance". | No probability or outcome in the code; nothing backtested; contradicted by the library's own failure modes. |
| R2 | "Buyers or sellers are significantly stronger." | Measures resting depth, not participants; "significant" is a fixed display gate. |
| R3 | Worked example: price "grinds into" the 2.5–5% zone. | The slices move with mid every bar; a fixed price level moves across slices instead. |
| R4 | Worked example: "sellers are leaning", "thicker shelf to land on". | Reads intent and a price path into a relative ratio. |
| R5 | "Narrow the window for scalping decisions." | Usage advice with no code or doc support. |
| R6 | v2 and v3 are "the same language". | Only the engine routing and this script's builtins were checked. v3 adds features and corrects eight TA builtins this script doesn't call. |
| R7 | Bare-hex colors (`a5d6a7`) are valid. | No page read confirms the form without `#`. |
| R8 | Any behavior of the unpasted plot section, including the final brace. | Not in the pasted source; recorded from the desk's paraphrase only. |
