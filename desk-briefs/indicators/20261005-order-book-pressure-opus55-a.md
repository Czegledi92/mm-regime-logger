# Order Book Pressure (OpenMarket library, kScript) — desk catalog note

- Status: paper note, research only. Not a strategy. No orders, no backtest, no notional, no edge claimed.
- Pass: independent pass A (opus55-a).
- Indicator: "Order Book Pressure", by openmarket, OpenMarket indicator library (page shown as "updated 1mo ago" in the user's screenshot).
- Inputs to this note: the kScript source the user pasted (reproduced below), and three screenshots of the library page.
- Doc fetches: 2026-10-04 22:55 UTC onward (the user's prompt dates its own fetch of the OpenMarket guide 2026-10-05).

## Bottom line

The script measures one thing: resting bid size against resting ask size, in up to four fixed distance bands from price (0–1%, 1–2.5%, 2.5–5%, 5–10%). It turns each band into an imbalance ratio from -100 to +100. Everything else is presentation: the colors, the opacity steps, the extreme highlighting, the reference lines, the scale factor, and the two "ratio minimum" thresholds. Only the two depth-window selects change which bands are measured. Nothing in the code estimates where price will find support or resistance, so the DESCRIPTION text's claim to that effect is refused (see "Library text vs code").

## Dialect

- The file header is `//@version=2`. The OpenMarket user guide calls the language kScript and shows its current editor template at `//@version=3`, using named arguments throughout: `define(title=..., position=..., axis=...)`, `ohlcv(symbol=..., exchange=...)`, `plotLine(value=..., width=..., colors=[...], label=[...], desc=[...])`. Source: https://openmarket.xyz/learn/core/k-script
- This script is kScript v2 by its own header. I found no v2→v3 changelog, so I do not treat v2 and v3 as interchangeable. Whether this script compiles unchanged under v3 is **unverified**.
- This script calls `define` and `input` partly with positional arguments, for example `define("Order Book Pressure", "onchart", axis=false)` and `input("posCol", "color", "a5d6a7", "Bid Fill Color")`. The v3 template I could read uses only named arguments. Positional acceptance in v2 or v3 is **unverified** against a reference.
- `static`, `sumBids`, `sumAsks`, and `input(type="select", options=[...])` signatures: **not verified**. The kScript language reference on docs.kiyotaka.ai returned HTTP 404 or 500 on every live fetch, and no archived copy was available (details in "Claims checked").

## What the code measures

Data subscriptions (initialization):

- `ob = orderbook(currentSymbol, currentExchange)`: the order book for the chart's own symbol and exchange. It is one venue and not aggregated, because no other exchange is subscribed.
- `px = ohlcv(currentSymbol, currentExchange)`; only `px.close` is used (`c`). Volume, high, and low are never read.

Cumulative depth, per bar:

- `cumBid_eN = sumBids(ob, eN)` and `cumAsk_eN = sumAsks(ob, eN)` for eN in {1, 2.5, 5, 10}.
- From the code alone, the second argument reads as a percent distance from a reference price, and the result as cumulative size out to that distance. The library text says the same ("sums bid depth and ask depth out to fixed distances from price: 1%, 2.5%, 5% and 10%"). **Not confirmed against kScript docs.** Also unconfirmed: (a) which reference price `sumBids` and `sumAsks` measure from (mid, best bid or ask, or last); (b) whether size is base or quote units; (c) whether the boundary is inclusive.
- The measurement anchor is not passed in. `c` is never given to `sumBids` or `sumAsks`. The reference lines are anchored on bar close `c`, but the depth sums are anchored wherever `sumBids` and `sumAsks` anchor internally. These two anchors can differ.

Band volumes are differences of cumulative sums:

| Band | Range | Bid volume | Ask volume | Enabled when |
| --- | --- | --- | --- | --- |
| A | 0–1% | `cumBid_e1` | `cumAsk_e1` | `d1 <= 0` and `1 <= d2` |
| B | 1–2.5% | `cumBid_e2 - cumBid_e1` | `cumAsk_e2 - cumAsk_e1` | `d1 <= 1` and `2.5 <= d2` |
| C | 2.5–5% | `cumBid_e3 - cumBid_e2` | `cumAsk_e3 - cumAsk_e2` | `d1 <= 2.5` and `5 <= d2` |
| D | 5–10% | `cumBid_e4 - cumBid_e3` | `cumAsk_e4 - cumAsk_e3` | `d1 <= 5` and `10 <= d2` |

Ratio per enabled band: `(bidVol - askVol) / (bidVol + askVol) * 100`. Disabled bands are hard-set to 0.

Properties that follow from the code:

- The ratio is bounded between -100 and +100. It is scale-free: two small orders can produce ±100, and the ratio carries no absolute size.
- Each band compares **two mirrored slices**: bids between x% and y% *below* the anchor against asks between x% and y% *above* it. A band is not a single price slice that holds both bids and asks.
- A band is enabled only when it lies fully inside the window [d1, d2]. Bands are never partially counted.
- With the defaults (`depth1 = 0%`, `depth2 = 5%`), bands A, B, and C are measured and band D is off. The worked example's three bands match this.
- With `depth1 = 10%`, no band can be enabled for any `depth2`, because `depth2` tops out at 10%. The same happens when `depth1 >= depth2`. Either way the indicator draws no fills and gives no warning.
- If a band holds zero size on both sides, the ratio is 0/0. The pasted code has no guard. What kScript does with that (NaN, Infinity, or an error) is undocumented here, so it is listed as unknown, not as a bug.
- Depth truncation is possible. The kScript v2 introduction (search-index copy) says order book access goes "up to 2,000 levels deep". If a book's 2,000 levels do not reach 5% or 10% from price, bands C and D undercount. Whether that happens depends on the venue, tick size, and how the platform buckets levels, none of which the script shows.
- History is unknown. The code does not show whether `orderbook(...)` yields a historical snapshot per bar or only the live book. Readings on past bars should not be assumed to be what the book showed at that bar's time until that is confirmed.

## What is only drawn

- Reference lines: `bidLineN = c * (1 - eN * scaleFactor / 100)` and `askLineN = c * (1 + eN * scaleFactor / 100)`. They are plotted only when `showRef` is on (per the user's summary of code not pasted verbatim). They follow bar close, so they move with price every bar even when the book does not change.
- Fill intensity (from the user's summary of the color functions, which were not pasted verbatim): |ratio| maps in 3.5-point steps from 0 to 70 onto color indexes 1–20 of rising opacity, and |ratio| ≥ 70 saturates. With `highlight` on, indexes 19–20 use `extremecol`. That corresponds to roughly |ratio| ≥ 63–66.5, depending on rounding that is not shown.
- Fill gate: a band fills only if its show flag is true and the ratio clears `minBidRatio` (bid color) or is at or below `-minAskRatio` (ask color). Whether "clears" means `>` or `>=` is not shown.
- Fill geometry: where on the chart each band's fill is drawn (between which lines, above or below price, or both) is in the part of the script not pasted. **Unconfirmed.**
- Truncation: the pasted script ends inside the band-4 block. A missing final closing brace is recorded as **unconfirmed**, not as a defect. No fix is proposed and the indicator is not rewritten.

## Settings: measurement vs display

| Setting (label) | Default | Changes the measurement? | Effect from code |
| --- | --- | --- | --- |
| Greater than or equal to (`depth1`) | 0% | **Yes** | Near edge of the window; enables or disables whole bands. |
| Smaller than (`depth2`) | 5% | **Yes** | Far edge of the window. The label says "smaller than", but a band whose outer edge *equals* `d2` is included (`e3 <= d2`). |
| Ratio minimum bids (`minBidRatio`) | 20 | No | Display gate for bid fills only; ratios are computed regardless. No constraint is declared in the code. |
| Ratio minimum asks (`minAskRatio`) | 20 | No | Display gate for ask fills only. |
| Band Scale Factor (`scaleFactor`) | 1, constraints 1–5 | No | Moves reference lines outward only. The depth sums always use fixed 1 / 2.5 / 5 / 10. |
| Show Reference Bands (`showRef`) | true | No | Shows or hides the level lines. |
| Highlight Extremes? (`highlight`) | true | No | Swaps the top two color steps to `extremecol`. |
| Bid Fill Color / Ask Fill Color / Extreme Color | `a5d6a7` / `f1627e` / `ffff00` | No | Colors only. |

## Library text vs code

Image 1 ("What it shows" plus the worked example):

- Agrees: fixed distances of 1, 2.5, 5, and 10%; per-band ratio of (bid − ask) / total in percent; positive means bids dominate; opacity steps of 3.5 points up to 70; top two steps switch to the extreme color when highlighting is on; scale factor 1 puts lines at the literal distances, and above 1 the liquidity is "still measured at the fixed depths".
- Imprecise: "that slice of the book". In the code each band pairs a bid slice below the anchor with an ask slice above it, so the two sides are mirrored slices, not one slice.
- Imprecise: "from price". The lines are drawn from bar close. The anchor that `sumBids` and `sumAsks` measure from is undocumented here.
- Worked example (labelled illustrative, 4h, window 0–5%): band A ≈ −40, band B ≈ +10, band C ≈ +55.
  - Consistent with the code: a 0–5% window enables exactly three bands.
  - Under the default thresholds (20 / 20), band A at −40 fills in the ask color (roughly step 11–12 of 20). Band B at +10 is **below `minBidRatio` and would not fill**; the text says it "prints", which does not conflict, but on the chart that band would be blank. Band C at +55 fills at roughly step 15–16, which is below the extreme steps. The text says "well up the intensity scale", which is consistent.
  - Whether the indicator "prints" a numeric ratio at all (label, legend, or data window) is not visible in the pasted code (`axis=false`). **Unconfirmed.**
  - Overclaim: "the heavier bid size sits several percent lower" and "a flush down has a thicker shelf to land on". A +55 ratio says only that bids exceed asks *in that mirrored band*. It says nothing about absolute bid size or about bids compared with other bands. Image 2 makes the same point ("Ratios are relative within a band"), so the library texts disagree with each other here, and the code supports image 2.
- "Read it as a map of where size is stacked, not as a signal": agrees with the code, with the caveat that the map is relative, not absolute.
- The chart image in image 1 did not render (it shows only the alt text "Order Book Pressure on BTCUSDT 1h"). No visual claim is drawn from it, and that symbol and timeframe are not used.

Image 2 ("When it fails" plus "Settings that matter"):

- Agrees: the bands are proportional to price and move with it (`c * (1 ± x)`); the ratio is relative and can go extreme in a thin band; the indicator ignores executed trades (only `orderbook` and `ohlcv.close` are read).
- "Depth is not commitment": a market-structure caveat that the code neither supports nor contradicts. Kept as is.
- Settings defaults, options, and range: all match the code.
- Overclaim: "Ratio minimum bids … floor before a band is treated as meaningfully bid-heavy". In the code it is only the threshold for drawing a fill. It is not a significance test, and it does not change the ratio.

Image 3 (DESCRIPTION):

- "Shows where buy and sell liquidity is stacked … at different depth levels (1%, 2.5%, 5%, 10%)": agrees.
- "Areas where buyers or sellers are significantly stronger": "significantly" is just the display threshold (default 20); no statistic is computed. Overclaim.
- "Which side of the market is heavier": partial. The comparison is per band and relative, with no cross-band or absolute total.
- "Where price is more likely to find support or resistance": **refused.** The code computes no probability and no price-reaction measure, and it never relates past readings to subsequent price. It also contradicts image 1's "not as a signal".

## Source as pasted (verbatim, truncated by the user)

```
//@version=2
define("Order Book Pressure", "onchart", axis=false);
var minBidRatio = input(name="minBidRatio", type="number", defaultValue=20, label="Ratio minimum bids");
var minAskRatio = input(name="minAskRatio", type="number", defaultValue=20, label="Ratio minimum asks");
var depth1 = input(name="depth1", type="select", defaultValue="0%", label="Greater than or equal to", options=["0%", "1%", "2.5%", "5%", "10%"]);
var depth2 = input(name="depth2", type="select", defaultValue="5%", label="Smaller than", options=["1%", "2.5%", "5%", "10%"]);
var posCol = input("posCol", "color", "a5d6a7", "Bid Fill Color")
var negCol = input("negCol", "color", "f1627e", "Ask Fill Color")
var extremecol = input("extremecol", "color", "ffff00", "Extreme Color")
var highlight = input(name="highlight", type="boolean", defaultValue=true, label="Highlight Extremes?");
var scaleFactor = input(name="scaleFactor", type="number", defaultValue=1, label="Band Scale Factor (1 = Fixed Scale)", constraints={min:1, max:5})
var showRef = input(name="showRef", type="boolean", defaultValue=true, label="Show Reference Bands")
timeseries ob = orderbook(currentSymbol, currentExchange);
timeseries px = ohlcv(currentSymbol, currentExchange);
var c = px.close;
static e0 = 0.0
static e1 = 1.0
static e2 = 2.5
static e3 = 5.0
static e4 = 10.0
static d1 = depth1 == "0%" ? e0 : depth1 == "1%" ? e1 : depth1 == "2.5%" ? e2 : depth1 == "5%" ? e3 : e4
static d2 = depth2 == "1%" ? e1 : depth2 == "2.5%" ? e2 : depth2 == "5%" ? e3 : e4
static enA = (d1 <= e0) && (e1 <= d2)
static enB = (d1 <= e1) && (e2 <= d2)
static enC = (d1 <= e2) && (e3 <= d2)
static enD = (d1 <= e3) && (e4 <= d2)
var bidLine1 = c * (1 - (e1 * scaleFactor) / 100.0)
var bidLine2 = c * (1 - (e2 * scaleFactor) / 100.0)
var bidLine3 = c * (1 - (e3 * scaleFactor) / 100.0)
var bidLine4 = c * (1 - (e4 * scaleFactor) / 100.0)
var askLine1 = c * (1 + (e1 * scaleFactor) / 100.0)
var askLine2 = c * (1 + (e2 * scaleFactor) / 100.0)
var askLine3 = c * (1 + (e3 * scaleFactor) / 100.0)
var askLine4 = c * (1 + (e4 * scaleFactor) / 100.0)
var cumBid_e1 = sumBids(ob, e1)
var cumBid_e2 = sumBids(ob, e2)
var cumBid_e3 = sumBids(ob, e3)
var cumBid_e4 = sumBids(ob, e4)
var cumAsk_e1 = sumAsks(ob, e1)
var cumAsk_e2 = sumAsks(ob, e2)
var cumAsk_e3 = sumAsks(ob, e3)
var cumAsk_e4 = sumAsks(ob, e4)
var bidVol_A = enA ? cumBid_e1 : 0
var askVol_A = enA ? cumAsk_e1 : 0
var bidVol_B = enB ? (cumBid_e2 - cumBid_e1) : 0
var askVol_B = enB ? (cumAsk_e2 - cumAsk_e1) : 0
var bidVol_C = enC ? (cumBid_e3 - cumBid_e2) : 0
var askVol_C = enC ? (cumAsk_e3 - cumAsk_e2) : 0
var bidVol_D = enD ? (cumBid_e4 - cumBid_e3) : 0
var askVol_D = enD ? (cumAsk_e4 - cumAsk_e3) : 0
var ratio1 = enA ? ((bidVol_A - askVol_A) / (bidVol_A + askVol_A)) * 100.0 : 0
var ratio2 = enB ? ((bidVol_B - askVol_B) / (bidVol_B + askVol_B)) * 100.0 : 0
var ratio3 = enC ? ((bidVol_C - askVol_C) / (bidVol_C + askVol_C)) * 100.0 : 0
var ratio4 = enD ? ((bidVol_D - askVol_D) / (bidVol_D + askVol_D)) * 100.0 : 0
```

User's prose summary of the remainder (not code; recorded as given): color functions `green_col_idx` and `red_col_idx` map |ratio| in 3.5-point steps from 0 to 70 onto indexes 1–20. The color arrays are 20 entries of rising opacity; with highlight on, the last two entries use `extremecol`. A band fills only when its show flag is true and the ratio clears `minBidRatio` (bids) or is ≤ `-minAskRatio` (asks). Reference lines plot only when `showRef` is on. The script ends inside the band-4 block.

## Claims checked

| Claim | Result | Source |
| --- | --- | --- |
| The language is called kScript, and it is OpenMarket's scripting language | Verified | https://openmarket.xyz/learn/core/k-script (live fetch OK) |
| The current editor template header is `//@version=3` | Verified (MA Cross template, verbatim) | https://openmarket.xyz/learn/core/k-script |
| v3 `define` uses `title=`, `position="onchart"`, `axis=` | Verified as named args in the template | https://openmarket.xyz/learn/core/k-script |
| v3 `plotLine(value=, width=, colors=[], label=[], desc=[])` | Verified in the template; the pasted script has no visible `plotLine` call to compare | https://openmarket.xyz/learn/core/k-script |
| `ohlcv(symbol=currentSymbol, exchange=currentExchange)` exists | Verified in the v3 template | https://openmarket.xyz/learn/core/k-script |
| `orderbook(symbol, exchange)` is the v2 order-book subscription | Search-index snippet only; live fetch returned 404 | https://docs.kiyotaka.ai/for-developers/k-script/updates/changelog |
| v2 introduced the per-bar execution model with separate `timeseries` declarations | Search-index snippet only; live fetch returned 404 | https://docs.kiyotaka.ai/for-developers/k-script/updates/changelog |
| kScript v2 order-book access goes "up to 2,000 levels deep" | Search-index snippet only; live fetch returned 500 | https://docs.kiyotaka.ai/for-developers/k-script/getting-started/introduction |
| v2 header is `//@version=2` with `define(title=..., position="onchart", axis=true)` | Search-index snippet only | https://docs.kiyotaka.ai/for-developers/k-script/getting-started/introduction |
| Settings defaults, options, and ranges in image 2 | Match the pasted code | Pasted source |
| Defaults enable bands A–C and disable D | Derived from the code | Pasted source (`enA`–`enD`) |
| `scaleFactor` affects only the drawn lines | Derived from the code | Pasted source (`bidLineN`/`askLineN` vs `sumBids`/`sumAsks`) |

## Claims refused or left unconfirmed

- The bands show "where price is more likely to find support or resistance" (image 3): **refused.** No probabilistic or price-reaction logic exists in the code.
- "Significantly stronger" (image 3) and "meaningfully bid-heavy" (image 2): **refused** as statistical claims. The code applies only a display threshold.
- Worked example: "thicker shelf" / "heavier bid size sits several percent lower": **refused.** The ratio is relative within a band, and image 2 says so too.
- `sumBids(ob, pct)` and `sumAsks(ob, pct)` signatures, reference price, units, and boundary inclusivity: **unconfirmed.** The kScript reference was unreachable. MobChart's docs (https://mobchart.com/docs/en/scripting/intro/) define a `ta.sumBids(orderbook, percent, price, inQuote)` and contain a near-identical banded-imbalance example, but MobChart is a different product, so it is **not used** as kScript evidence.
- Grokipedia's kScript page and Tape Delta's `plotLine` and `input` docs: **not used.** They are tertiary or describe a different language.
- That `static`, positional `input(...)`, positional `define(...)`, and `input(type="select")` behave as written in v2, or carry over to v3: **unconfirmed.**
- That v2 and v3 are equivalent for this script: **unconfirmed.** No v2→v3 changelog was found.
- That `orderbook(...)` provides historical per-bar snapshots: **unconfirmed.**
- Behavior when a band has zero size on both sides (0/0): **unconfirmed**; no guard appears in the pasted code.
- Fill geometry, numeric ratio display, and `>` vs `>=` in the fill gate: **unconfirmed**; that code was not pasted.
- A missing final closing brace: **unconfirmed**. It is not treated as a bug, and no fix is proposed.
- Any price, symbol, edge, trading rule, backtest, or notional: **none stated.** The "BTCUSDT 1h" alt text in image 1 is not used.
