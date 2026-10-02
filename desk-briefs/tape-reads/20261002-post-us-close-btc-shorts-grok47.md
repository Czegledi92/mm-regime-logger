# Tape read — Binance BTCUSDT perpetual, post–US cash close, 2 Oct 2026

PAPER / observational only. No orders, no size, no firm identified. Two stills from the desk, plus the public 1-minute Binance USDT-M tape used only to put a clock on prints the boards already show. Where the still and the tape disagree, both numbers are kept and the disagreement is named.

**Where the operator hypothesis lands.** The fresh-short read is right, and it is specific. Bid-side size was on the screen at 16:30 ET, inside a thick yellow liquidity band around 84,300–84,320, with the 0–5% book-depth delta at **+94.86M**. That minute itself did not consume the band: it closed **up** $22.20 on 379.67 BTC, while taker flow was only mildly offered. The consumption is the **16:41 ET** minute. On the public perp tape that minute is 1,536.8 BTC, **94.7% taker sell** (−1,372 BTC, about **$116M** net at the close), price from 84,391 to a 84,249.8 low, and open interest **up 967 BTC**. Forced long liquidations on that minute are **0.30 BTC**. A second, smaller sweep at **17:26 ET** (358 BTC sold, 24 BTC bought, about **$28M** net) is the print that belongs next to the highlighted **−25M** box. Open interest rose only **67 BTC** on that bar, and forced liquidations stayed near zero. So the later clip is a real aggressive sell into a shown bid, and it is not a second wave of fresh shorts and not a liquidation cascade.

---

## 1. Scene-set

**Venue and product.** Both boards are labeled **BTCUSDT**, **Bitcoin**, **1m**. The CVD strip is tagged **binance.f**. The crosshair bars match Binance USDT-M **perpetual** BTCUSDT to the cent, including volume and open interest (section 9). This is the perp, not the spot book. Spot is used later only as a control, and it did not trade this size.

**Clocks.** The chart footer is **UTC−4**, which is America/New_York on this date (EDT). Vienna is CEST, **UTC+2**, six hours ahead of the footer. US cash equities were already closed (16:00 ET). CME Bitcoin futures were still in their Friday session at 16:30 ET and at the 16:41 sweep; the Friday halt is 16:00 America/Chicago, which is **17:00 ET**. Both stills were captured after that halt. The footer on both says **CME opens 2d**, which lines up with the Sunday 18:00 ET reopen.

| Mark | New York (EDT) | UTC | Vienna (CEST) | What it is |
| --- | --- | --- | --- | --- |
| Cash equity close | 16:00 | 20:00 | 22:00 | Already done before either crosshair |
| Board 1 crosshair | 16:30:00 | 20:30 | 22:30 | Footer: “1h 2m ago” |
| Sweep through the bid | 16:41 | 20:41 | 22:41 | Public tape; the long red candle on board 1 |
| Session low on the board | 16:43 | 20:43 | 22:43 | Low tag **84,188.80** |
| CME BTC Friday halt | 17:00 | 21:00 | 23:00 | Perp keeps trading; listed futures do not |
| Board 2 crosshair | 17:25:00 | 21:25 | 23:25 | Footer: “4m 47s ago” |
| −25M-class minute | 17:26 | 21:26 | 23:26 | Public tape; the highlighted box is on this board |
| Board 2 captured | 17:29:47 | 21:29:47 | 23:29:47 | Ping 133 ms. Trade-balance countdown “in 3d 15h” |
| Board 1 captured | 17:32:17 | 21:32:17 | 23:32:17 | Ping 128 ms. Countdown “in 3d 14h” |

Board 1 was shot later and is the wide view (16:30 crosshair, the sell, and the bounce). Board 2 was shot three minutes earlier and is zoomed on the 17:25 area, with the operator’s white box around **−4M** and **−25M** and an arrow into the yellow footprint cells at 84,450.

**Levels on the boards.**

| Level | Board 1 (16:30 crosshair, shot 17:32) | Board 2 (17:25 crosshair, shot 17:29) |
| --- | --- | --- |
| Session VWAP | **85,740.86** | **85,699.91** |
| Weekly open | **84,433.00** | **84,433.00** |
| Crosshair OHLC | 84,310.20 / 84,332.40 / 84,300.00 / 84,332.40 | 84,450.90 / 84,450.90 / 84,450.80 / 84,450.80 |
| Crosshair change | **+22.20 (+0.03%)** | **−0.10 (−0.00%)** |
| Crosshair volume | **379.67** | **48.65** |
| Live price at capture | **84,403.30** (cyan) | **84,404.10** (cyan) |
| High tag | not labeled; axis top grid 84,480 | **84,475.50** |
| Low tag | **84,188.80** | **84,389.50** |
| Bell / alert | **84,303.96** | **84,446.72** |
| CVD BTC at crosshair | **−2,416.51** | **−2,567.96** |
| CVD series tag | binance.f **−2.9K** | binance.f **−2.9K** |
| Open interest at crosshair | O 96,369.78 H 96,533.94 L 96,369.78 C 96,529.40 | O 98,784.26 H 98,798.22 L 98,784.16 C 98,797.92 |
| OI right-edge tag | **b 98.8K** | **b 98.8K** |
| Book depth 0–5% delta | **+94.86M** at the crosshair; right edge **30.39M** | **+40.31M** at the crosshair; right edge **29.85M** |

VWAP near 85,700 against price near 84,300–84,450 is a gap of roughly **1,250 to 1,450 points**. The market the seller hit was already a long way under the session average. Selling there is not a VWAP schedule catching up to value. It is selling a market that has already spent the session offered.

The weekly open at 84,433 sits in the middle of everything that follows. Price was under it at 16:30 (close 84,332), lost it by a wide margin at 16:43 (84,189), had reclaimed it by the time board 2’s high tag printed (84,475.50), and was back **under** it at both capture prices (84,403 and 84,404).

Indicators toggled on both boards: Order Book Pressure, VWAP, Key Levels, Agg. Volume Footprint, Order Book Heatmap. Four indicators are flagged in the header cluster. No legend on the still defines the heatmap colors. The yellow bands behave as resting bid interest: they sit under price, they are continuous through the left and center of board 1, and the sell candle trades down through them. Purple and teal ovals are sparse and are not read as a second book.

---

## 2. Bar-by-bar / clip-by-clip chronology

Two layers stay separate. **Read** means it is on the still. **Tape** means it is the public Binance USDT-M 1-minute aggregate, used because the crosshair bars match the still exactly, so the minutes to the right and left of the crosshair can be named. Delta boxes on the still are transcribed in the appendix. Their K/M glyphs are quote-currency size (a −25M BTC delta is impossible; CVD is the series that is explicitly in BTC). A compressed 1-minute axis stacks those boxes vertically, so a column of labels is not assumed to be one-label-per-minute unless the tape makes the minute obvious.

### 2.1 Before the crosshair — the up-sweep that failed (16:23–16:29 ET)

This is left of the board 1 crosshair. It is on the wide still as the upper delta field and the start of the yellow band. The tape gives the minutes.

| ET | UTC | Perp price (O → H / L → C) | Volume BTC | Taker buy / sell BTC | Coin delta | OI close (BTC) | OI change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 16:23 | 20:23 | 84,341.7 → 84,466.2 / 84,341.7 → 84,443.3 | 488.6 | 412.8 / 75.8 | **+337.0** | 95,782.9 | +86 from 20:22 |
| 16:24 | 20:24 | 84,443.3 → **84,506.6** high / 84,412.1 → 84,473.2 | 669.1 | 484.0 / 185.1 | **+298.9** | 96,042.9 | +260 |
| 16:25 | 20:25 | 84,473.3 → 84,506.0 / 84,445.0 → 84,480.8 | 286.3 | 196.3 / 90.1 | **+106.2** | 96,167.0 | +124 |
| 16:26 | 20:26 | 84,480.7 → 84,500.1 / 84,480.7 → 84,480.7 | 99.3 | 34.2 / 65.1 | −31.0 | 96,130.9 | −36 |
| 16:27 | 20:27 | 84,480.8 → 84,480.8 / **84,362.7** → 84,395.0 | 439.7 | 76.6 / **363.2** | **−286.6** | 96,207.1 | +76 |
| 16:28 | 20:28 | 84,395.0 → 84,395.1 / 84,305.4 → 84,334.1 | 248.9 | 54.2 / 194.6 | **−140.4** | 96,317.9 | +111 |
| 16:29 | 20:29 | 84,334.2 → 84,334.2 / 84,310.1 → 84,310.1 | 147.4 | 31.4 / 116.0 | **−84.7** | 96,369.8 | +52 |

Read as a clip, not as seven isolated bars. From 16:23 to 16:25 the perp lifts off ~84,340 through the weekly open and tags **84,506.6**. Net taker delta over 16:23–16:26 is about **+711 BTC**. Open interest rises about **+434 BTC** from the 16:22 close (95,696.9) to the 16:26 close (96,130.9). Price up, aggressive buying, OI up: new long exposure is the clean read of the up-sweep. Forced short liquidations in that burst are noise (well under 1 BTC).

Then 16:27–16:29 give it back. Three minutes, net taker delta **−512 BTC**, price from a 84,481 open down to a 84,310 close, and OI **still rising** (+239 BTC from the 16:26 close to the 16:29 close). That is the first short-initiation clip of the hour. It lands in the same 84,300–84,360 pocket the heatmap is painting yellow. About **$24M** of net sell notional on 16:27 alone (286.6 BTC times that minute’s 84,395 close) sits next to the **−23M** glyph in the red stack. The still does not label that box with a timestamp; the neighborhood is the match, not a claim that the glyph’s accounting identity was audited.

Spot on these minutes is a different market. Spot’s 16:24 high is 84,528.51 on 24 BTC. Spot’s 16:27 low is 84,408 on 19 BTC. The perp traded through prices the spot book barely visited. The failure from 84,507 was a perp event.

### 2.2 The 16:30 crosshair — absorption, with the bid still winning

**Read, board 1.** Crosshair parked on **Fri 02 Oct 2026 16:30:00**.

- Price: O 84,310.20, H 84,332.40, L 84,300.00, C 84,332.40, **+22.20 (+0.03%)**, volume **379.67**.
- Open interest on that bar: O **96,369.78**, H **96,533.94**, L **96,369.78**, C **96,529.40**. The low equals the open. The bar only added interest. (A small digit in “L” can be misread as 96,389.78. The public bar’s low is 96,369.78, identical to the open, and the other three prints match the still. The low-equals-open reading is the one that survives.)
- CVD BTC **−2,416.51**. The line to the left of the crosshair is flat-to-heavy. The drop on the CVD panel is to the **right** of this timestamp.
- Book-depth delta **+94.86M**, the high area of that histogram.
- Footprint ladder and the “UNFINISHED AUCTION” flag sit on this part of the chart. Cells in section 3.
- Yellow bands run horizontally through 84,300–84,360 at this x-position.

**Tape, same minute.** Taker buy **160.6 BTC**, taker sell **219.1 BTC**, coin delta **−58.6 BTC** (about **−$4.9M** at the 84,332 close). OI **+159.6 BTC**. Price closed up.

So the minute the operator froze is a pause with a bid that is being hit and is still lifting the close. Aggressive flow is offered. Open interest is expanding. The passive side is taking the sell and price is not falling. That is the opposite of a finished breakdown, and it is also the opposite of a quiet, balanced chop: 379 BTC in one minute is the largest bar since the 16:24 surge, and 58% of it is taker sell, and the close is still green.

The hypothesis that “fills” happened on this bar overstates it. The showing is here. The fill that clears the level is eleven minutes later.

### 2.3 16:31–16:40 — coil on the band

Tape, summarized because the still’s delta boxes in this stretch are the smaller K and low-M labels, not a single climax.

Price drifts from the 16:30 close of 84,332 up to a 16:40 close of 84,391, with a local high of 84,418.8 at 16:33. Volumes fall to 20–70 BTC a minute. OI creeps from 96,529 to **96,652** (+123). No liquidation print of size. The yellow band is still the feature on the chart. Depth, on the still, is still in the elevated part of the histogram through this left-center region; the step-down is further right, with the sell candle.

This is the part of the story that looks like a desk waiting. Ten minutes of a displayed bid, a grind back toward 84,400, weekly open still overhead at 84,433, VWAP still 1,300 points up.

### 2.4 16:41–16:43 — the sweep

**Read, board 1.** To the right of the footprint, a single long red candle runs down through the yellow bands. The low is tagged **84,188.80**, and the same price is printed beside the wick. Above that candle, a vertical stack of red delta boxes, confirmed on a tight crop: **−23M, −18M, −12M, −21M, −13M, −5M**, with **−805K, −570K, −863K, −264K, −50K** in the same column, then **−2M / −3M / −2M** lower on the wick, plus small green remnants (**633K, 602K, 12K, 458K, 1M**). The stack is one visual column. It should be read as “this is where the multi-million offer labels concentrate,” not as a guaranteed top-to-bottom minute sequence.

**Tape.**

| ET | Perp O / H / L / C | Volume | Buy / sell BTC | Coin delta | Approx net notional at the close | OI close | OI vs prior close | Long liquidations (sell-side, BTC) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 16:41 | 84,391.0 / 84,391.1 / **84,249.8** / 84,260.7 | **1,536.8** | 82.2 / **1,454.6** | **−1,372.4** | **about −$116M** | **97,619.4** | **+967.3** | **0.301** |
| 16:42 | 84,260.7 / 84,260.7 / 84,240.0 / 84,241.8 | 88.6 | 31.2 / 57.4 | −26.2 | about −$2.2M | 97,610.6 | −9 | none |
| 16:43 | 84,241.7 / 84,249.1 / **84,188.8** / 84,204.7 | 440.4 | 161.8 / 278.6 | **−116.8** | about −$9.8M | 97,661.1 | +50 | **2.016** |

16:41 is the event. One minute, about seventeen times the 16:42 volume, **94.7% of the contracts sold by takers**. Price travels about 141 points. Open interest jumps by **967 BTC**, roughly **$82M** of new open interest at that minute’s close. The sell is larger than the OI jump (1,455 BTC sold versus 967 BTC of new OI), so the whole sell was not “every lot opened a new short against a new long.” A slice of the sell closed existing longs, or opened shorts against positions that were themselves closing. The net position of the market still got larger, in the direction of the aggressive sell.

Forced liquidations do not explain it. The largest sell-side liquidation print in the entire two-hour window is **2.02 BTC** at 16:43, against 279 BTC of taker selling in that minute and 1,455 BTC the minute before. Sum of all sell-side liquidation prints from 16:00 to 17:49 ET is **2.44 BTC**. Sum of buy-side liquidation prints (shorts forced out) is **0.91 BTC**.

Spot control, same minutes:

| ET | Spot low | Spot volume | Spot taker delta | Perp low | Perp volume |
| --- | --- | --- | --- | --- | --- |
| 16:41 | 84,289.40 | 31.4 BTC | about −$0.67M | 84,249.8 | 1,536.8 BTC |
| 16:43 | 84,232.01 | 28.5 BTC | about −$0.75M | **84,188.8** | 440.4 BTC |

The perp low undercuts the spot low by about **$40** at 16:41 and about **$43** at 16:43. Spot’s combined volume on those two minutes is about 60 BTC. The perp’s is about 2,000 BTC. Whoever hit the bid was trading the perpetual. A cash seller of this size would have shown up on BTCUSDT spot. They did not.

### 2.5 16:46–16:47 — the bounce that adds interest instead of releasing it

**Read.** The right half of board 1, after the 84,188.80 wick, is a run of green delta boxes: repeated **2M, 3M, 4M, 5M, 6M, 7M**, with a minority of red labels (**−822K, −395K, −112K, −425K, −80K, −245K, −2M**). Price trades back up through the bell at 84,303.96. By the 17:32 capture the live price is **84,403.30**, just under the weekly open. CVD has turned up off its low and has not returned to the 16:30 reading of −2,416. The right-edge CVD tag is still **−2.9K**. The depth histogram is on its lower step; the right-edge print is **30.39M**.

**Tape.**

| ET | Perp path | Volume | Buy / sell | Coin delta | Approx notional | OI close | OI change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 16:46 | 84,219.5 → 84,358.6 high / 84,199.2 low → 84,345.9 | 755.2 | **678.2 / 76.9** | **+601.3** | about **+$51M** | 97,966.9 | **+311** from 16:45 |
| 16:47 | 84,345.9 → 84,387.0 / 84,320.0 → 84,366.3 | 527.8 | **461.7 / 66.1** | **+395.6** | about **+$33M** | **98,454.3** | **+487** |

Price up, aggressive buying, OI up again, by about **+800 BTC** across the two minutes. That is new long exposure on the bounce. It is not shorts buying their inventory back. A cover would have taken OI down from the 97,661 post-sweep shelf. OI left that shelf upward.

The shorts who sold 16:41 (fills from roughly 84,391 down to 84,250, with the extension to 84,189 at 16:43) were, by 16:47, watching a bounce of about 180 points off the low with **more** open interest, not less. The inventory stuck.

### 2.6 16:48–17:25 — sticky OI, price back above the weekly open

Tape, condensed. OI peaks near **98,931** at 16:59–17:00 ET (98,931.3 close at 16:59, 98,927.3 at 17:00) and then leaks slowly. By the 17:25 crosshair it is **98,797.9**. That is still about **2,150 BTC** above the 16:40 pre-sweep level of 96,652, and about **3,240 BTC** above the 16:00 ET level of 95,555.

Price spends 17:00–17:18 grinding 84,450–84,485. The high of this whole rebound, and the high tag on board 2, is **84,475.50**, printed at **17:18 ET** (perp high 84,475.5). From 17:20 through 17:25 the market compresses onto a single tick area at **84,450.8–84,451.5**. Volumes: 7.7, 17.3, 27.5, 62.5, 32.9, then the crosshair bar.

**Read, board 2, the 17:25 bar.** O 84,450.90, H 84,450.90, L 84,450.80, C 84,450.80, **−0.10**, volume **48.65**. Ten cents of range. OI O 98,784.26 / H 98,798.22 / L 98,784.16 / C 98,797.92, a **+13.7 BTC** wiggle. CVD **−2,567.96**, and on this zoomed panel the line is gently lower across the view. Depth delta **+40.31M**, less than half the 16:30 reading. Weekly open is just underneath, at 84,433. The bell sits at 84,446.72, i.e. on top of this coil. High tag 84,475.50, low tag 84,389.50 (that low belongs to the next few minutes, not to this bar).

**Tape, 17:25.** Taker buy **2.4 BTC**, taker sell **46.2 BTC**. **95% of the minute is taker sell, and the price range is one tick.** The bid at 84,450.80 absorbed it. This is the cleanest “shown bid, then hit, and the bid held” print on either board. It is small compared with 16:41. It is the same behavior.

### 2.7 17:26 — the highlighted −25M, and what it actually did to OI

**Read, board 2.** Operator overlay: a white rectangle around **−4M** and **−25M**, arrow down into the footprint row at **84,450.00**, where **315.66** and **302.42** are both highlighted yellow and the third cell is **15.09**. Along the top of this zoom, left to right: **254K** (green), **−577K**, **−381K**, **−1M**, **−719K**, **748K** (green), **−2M**, **−4M**, **−25M**. Under the red candle: **−557K, −247K, −525K**, then **−2M** and **1M** on the body, then a lower cluster **−495K, −828K, 465K, 375K, 476K, 203K, 438K**, with **84,389.50** marked on the wick. The chart’s Low tag is the same **84,389.50**. Live price at the 17:29:47 capture is **84,404.10**.

The 17:25 crosshair bar cannot own the footprint rows away from 84,450. That bar’s entire range is 84,450.80–84,450.90. Volume printed on the ladder at 84,435, 84,440, 84,445, 84,455, 84,460, and 84,465 belongs to other minutes. The ladder is a cluster around the highs, not a one-bar profile of the doji. Column headings are not printed, so 315.66 versus 302.42 is not labeled bid versus ask. What is safe: both cells are an order of magnitude larger than every other cell in the ladder, they sit on the price where the coil and the next minute’s open both trade, and 315.66 BTC at 84,450 is about **$26.6M** of notional if the cell is in coin. That is the same neighborhood as the **−25M** tag. It is an inference about units, and the still does not print a unit on the cell.

**Tape, the minute after the crosshair.**

| ET | Perp O / H / L / C | Volume | Buy / sell | Coin delta | Approx notional | OI | Long liq |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 17:26 | 84,450.8 / 84,450.9 / **84,392.3** / 84,405.5 | 382.4 | 24.2 / **358.2** | **−333.9** | **about −$28.2M** | 98,797.9 → **98,865.1** (**+67**) | none on 17:26; 0.056 BTC at 17:27 |
| 17:29 | 84,399.7 / 84,404.6 / **84,389.5** / 84,404.1 | 61.2 | 30.5 / 30.7 | −0.2 | flat | 98,826.4 | none |

17:26 is the only minute in the board 2 window with a net sell in the mid-tens of millions. The **−25M** glyph and the **−$28M** tape figure are the same clip. They are not the same accounting identity: the board’s aggregation (filtering, which trades it drops, whether the box is a price-level delta or a bar delta) is not documented on the still. The clock and the magnitude match. The low tag 84,389.50 is the 17:29 wick, a few dollars under the 17:26 low, on much less size.

OI **+67 BTC** on a 358 BTC taker sell is the important divergence from 16:41. The aggressive sell is real. The new-position add is small. Forced liquidation is absent. The coherent read is a hit into a bid that had just proven itself on the 17:25 doji, with a large share of the sell closing existing longs or crossing against other closing flow, and only a thin slice of new short. Price stopped about **$45** under the open (84,450.8 to a 84,405.5 close) and about **$58** under it at the low (84,392.3). Compare 16:41, where a similar “someone hit the bid” story traveled 141 points and added 967 BTC of OI.

Spot at 17:26: low **84,431.79**, volume **11.6 BTC**, delta about **−$0.60M**. The perp low was 84,392. Another perp-only print, another ~$40 under the spot low.

### 2.8 What the tape did after the stills were shot

Board 2 is 17:29:47. Board 1 is 17:32:17. This is not on either picture. It matters for the “did the short stick” question, so it stays in its own paragraph.

From 17:30 to 17:41 ET the perp trades back up and prints a high of **84,523.6** at 17:41, a few dollars through the 16:24 high of 84,506.6. OI does not expand with it. OI at 17:26’s close was 98,865; by 17:49 it is **98,582.6**, a bleed of about **280 BTC**, and still about **3,000 BTC** above the 16:00 ET area near 95,555 (that minute opened 95,573 and closed 95,555). The post-capture rally repaired the price of the 17:26 sweep and tested the afternoon high. It did not take the 16:41 open interest out.

---

## 3. Liquidity story

### What was showing

At the 16:30 crosshair the platform’s own 0–5% order-book depth delta is **+94.86M**, and the histogram behind it is at the highs of the panel (the axis marks 80M). The sign convention is the panel’s: the value is positive and the bars are the same teal used for positive delta elsewhere. Standard reading of a panel titled this way is bid depth minus ask depth inside 5% of mid. The still has no legend, so the sign is taken as printed: a large positive number that later shrinks.

The heatmap at that same x-position is a stack of yellow horizontal bands from roughly the mid-84,200s through the mid-84,300s, continuous in time across the left and center of board 1. Price at 16:30 (84,300–84,332) is sitting **inside** the upper part of that stack, not approaching it from above after a long fall. The band was already there while the 16:23–16:26 rally was failing back into it.

There is a second showing, smaller and later, on board 2. A yellow band runs along ~84,446–84,450, exactly where the 17:20–17:25 coil sits and where the bell is set (84,446.72). Depth delta at that crosshair is **+40.31M**. Still bid-heavy on the panel’s sign. Less than half the 16:30 cushion.

By the right edge of both stills the depth delta is about **30M** (30.39M on board 1, 29.85M on board 2). Those two right-edge figures are axis tags, slightly softer than the crosshair readouts, and they agree with each other. The cushion on the panel thinned by on the order of **60M** between the 16:30 crosshair and the end of the view.

### Who was passive, who was aggressive

| Clip | Aggressive side (taker) | What price did | What that says about the passive side |
| --- | --- | --- | --- |
| 16:30 | Sell, 219 vs 161, mild | Close **up** $22 | Passive bid lifted the market while being hit. The bid won the minute. |
| 16:41 | Sell, 1,455 vs 82 | Down ~141 points | The bid traded, then lost. 1,537 BTC going through in one minute is a fill, not a flicker of a quote. How much additional size was **pulled** rather than filled is not visible. Cancels are not in the data. |
| 16:43 | Sell, 279 vs 162 | Extends the low to 84,188.80 | Follow-through under the broken band. Real size, an order of magnitude smaller than 16:41. |
| 16:46–16:47 | Buy, 678 vs 77, then 462 vs 66 | Up ~180 points off the low | Passive offers got lifted. Given OI rose, a good share of those offers were new shorts or were not pure covers. |
| 17:25 | Sell, 46 vs 2, **95%** | **Unchanged** (one tick) | Passive bid at 84,450.80 absorbed a one-sided minute without giving a price. |
| 17:26 | Sell, 358 vs 24, **94%** | Down to 84,392, close 84,406 | The same pocket gave way. Travel was limited. OI barely rose. |

“Consumed” is the right verb for 16:41 because the volume is undeniable and the level did not hold. “Only pulled, nothing traded” is not available as a description: the contracts traded. “Every displayed lot was a sincere resting bid that sat there for eleven minutes” is also not available: the still cannot show modifications and cancels inside the minute, and eleven minutes is long enough for a quote to be replaced several times. What the depth panel and the tape agree on is the sequence **displayed cushion → one-sided trade → thinner cushion and a lower price**.

### The footprint, including the unfinished auction

Board 1 footprint, read off a magnified crop. The **223.57** cell was checked glyph by glyph (the leading “223” and the “.57” sit in adjacent yellow cells split by the crosshair). Three number columns and a price. The platform does not label the columns on this still. Highlighted cells are yellow. The boxed **11.57** is the hover (“Shift for lens”).

| Price | Col A | Col B | Col C |
| --- | --- | --- | --- |
| 84,320.00 | partly hidden (3.62 at the edge) | hidden under the tooltip | **158.13** yellow |
| 84,315.00 | 11.01, partly hidden | 12.59, partly hidden | 9.61 |
| 84,310.00 | 15.10 | **223.57** yellow | **215.05** yellow |
| 84,305.00 | 4.80 | **11.57** boxed | 9.26 |
| 84,300.00 | 20.36 | **147.20** yellow | **143.89** yellow |
| 84,295.00 | 10.58 | 13.30 | 13.48 |
| 84,290.00 | 25.69 | 18.34 | 24.35 |

The tooltip over the bucket **84,299.95–84,309.95** reads **667K × 5.20M**, delta **+4.50M**, sum **5.90M**. The arithmetic is internal and consistent: 5.20M − 0.667M = 4.533M, which rounds to the printed +4.50M, and 5.20M + 0.667M = 5.867M, which rounds to the printed 5.90M. It is a two-sided size at that 10-point bucket, with one side about eight times the other, the larger side on the positive-delta side of the tooltip. The tooltip does not say “resting” or “traded” in words. It sits on top of both the heatmap and the footprint. Treat it as the platform’s bucket readout, not as a reconstructed order-id history.

The words **UNFINISHED AUCTION** are printed on the ladder. In auction terms that means the extreme of the profile did not finish with a one-sided excess: both sides traded at the high or the low, so the auction did not close. The bottom row at 84,290 still has size in every column (25.69 / 18.34 / 24.35). The heavy rows at 84,300 and 84,310 are large on **both** of the big columns (223.57 against 215.05, 147.20 against 143.89). That is a two-sided node, not a one-sided sweep print. It matches the 16:30 tape: lots of trade, both ways, price held.

One limit, stated plainly: those two 84,310 cells already sum to 439, and the 16:30 bar’s exchange volume is 379.67. They cannot both be subsets of that single minute. The ladder is a cluster wider than the crosshair candle (the prices run down to 84,290, and the 16:30 low was 84,300.00). Read the ladder as the profile of the pause, not as a reconciled audit of one official bar.

Board 2 footprint, same three-column layout:

| Price | Col A | Col B | Col C |
| --- | --- | --- | --- |
| 84,465.00 | 10.52 | 5.51 | 9.44 |
| 84,460.00 | 8.72 | 10.19 | 12.31 |
| 84,455.00 | 11.70 | 18.17 | 3.45 (last digit is the soft one; a second pass looked like 3.48) |
| 84,450.00 | **315.66** yellow | **302.42** yellow | 15.09 |
| 84,445.00 | 1.60 | 1.84 | 23.96 |
| 84,440.00 | 14.49 | 7.55 | 5.31 |
| 84,435.00 | 14.30 | 13.23 | 18.87 |

If the first two columns are the two sides of an aggregated profile, 84,450 is a **balanced** high-volume node (315.66 against 302.42, net about 13) sitting on top of a minute whose **bar** delta was about −334 BTC. Both can be true: the opens traded both ways in huge size at 84,450, and the net sell was produced as price left that price and traveled to 84,392, below the bottom of this ladder (the ladder stops at 84,435). The arrow the operator drew is then a link between “where the size was” and “the minute’s net,” not a claim that one yellow cell equals −25M by itself. If instead each yellow cell is a separate one-sided print, each is about $25–27M of notional and the −25M tag is one of them. The still does not decide. The tape decides the minute: 17:26, −334 BTC, about −$28M, OI +67.

---

## 4. Positioning triad

Coin delta is taker buy minus taker sell, from the public trade aggregate. Notional is that coin delta times the minute’s close, so it is a reconstruction, not Binance’s official quote-volume delta. Inside these minutes the price range is tight enough that the reconstruction is good to a couple of percent. Open interest is in BTC. Liquidations are the venue’s liquidation aggregate; sell-side means a long closed by a forced sell.

| Phase (ET) | Price | CVD / taker delta | Open interest | Liquidations | Read |
| --- | --- | --- | --- | --- | --- |
| 16:00–16:22, background | Pinned 84,270–84,390 | Small, mixed. Window starts with OI 95,555 | +142 BTC drift to 16:22 | Dust | Positioning already built earlier in the day. Session CVD on the board is already −2,416 BTC by 16:30. This hour did not dig that hole. |
| 16:23–16:26 up-sweep | 84,342 → **84,506.6** | **+711 BTC** over the four minutes | **+434 BTC** | Short liqs under 1 BTC | Price up, delta up, OI up. New longs. |
| 16:27–16:29 first sell | 84,481 → 84,310 | **−512 BTC** | **+239 BTC** | None of size | Price down, delta down, OI up. First fresh-short clip. Lands in the yellow band. |
| **16:30 crosshair** | **Up** $22 to 84,332 | **−59 BTC** (board CVD −2,416.51) | **+160 BTC** to 96,529 | None | Price up, delta down, OI up. Absorption. Aggressive sells are opening or closing; the passive bid is lifting. The short is leaning, the bid has not broken. |
| 16:31–16:40 coil | 84,332 → 84,391 | Quiet | +123 BTC to 96,652 | None | Waiting. Cushion still displayed. |
| **16:41 sweep** | **Down** ~141 pts to 84,250, close 84,261 | **−1,372 BTC**, about **−$116M** | **+967 BTC** to 97,619 | **0.30 BTC** long liq | Price down, delta down, OI up, liqs absent. **Fresh shorts, hit-the-bid.** The cleanest print of the day on this question. |
| 16:43 low | Low **84,188.80** | −117 BTC | +50 BTC | 2.02 BTC long liq | Extension. Still not a cascade. The 2 BTC liquidation is the largest forced print of the window and it is a rounding error on the volume. |
| **16:46–16:47 bounce** | Up to ~84,366 | **+997 BTC**, about +$84M | **+799 BTC** to 98,454 | None of size | Price up, delta up, OI up. **New longs.** The 16:41 short is not covering. |
| 16:48–17:18 repair | Back to **84,475.50** high at 17:18; OI peaks ~**98,931** at 17:00 | Net bought, smaller clips | OI sticks, then leaks ~130 BTC into 17:18 | Dust | Short inventory from the sweep is still inside the open interest. New longs from the bounce are too. |
| **17:25 doji** | Unchanged, 84,450.80–84,450.90 | −44 BTC, **95% sell**, 48.7 BTC total (board CVD −2,567.96) | +14 BTC, level 98,798 | None | Bid absorbing. Depth delta still +40M. |
| **17:26 −25M clip** | Down to 84,392, close 84,406 | **−334 BTC**, about **−$28M** | **+67 BTC** | ~0 (0.06 BTC the next minute) | Price down, delta down, OI flat. Aggressive sell, **not** a fresh-short add of the 16:41 kind, **not** a forced liquidation. Closing flow plus a thin OI residual. |
| 17:27–17:49, after the stills | Low 84,389.5 at 17:29; later high **84,523.6** at 17:41 | Bought back | OI bleeds 98,865 → **98,583** | None of size | Some cover after 17:26. The 16:41 add is still in the number. Price has repaired through the weekly open and tagged the afternoon high. |

The triad the desk already had — price down, CVD down, OI up, fresh shorts — is the right description of **16:27–16:29** and, much more clearly, of **16:41**. It is the wrong description of **17:26**, where OI refused to confirm, and it is the wrong description of the bounce, where the same triad with the signs flipped says new longs.

A boundary on the phrase “fresh shorts.” OI up on a sell bar means new positions were opened on net. It does not, by itself, identify the passive counterparty. The aggressive side was the seller, and the seller’s sales exceeded the OI increase (1,455 versus 967 at 16:41), so part of the tape was longs closing. The passive bid can have been a new long, a market maker who hedged elsewhere, or a short covering into the seller — except a cover on the bid would be a passive buy closing a short, which **reduces** OI, and OI rose, so passive short-covering cannot have been the whole other side. New shorts were opened. New longs on the bid are allowed by the same arithmetic. Both can be in the print. What is not in the print is a long-liquidation cascade.

Funding, for context only, stayed a small positive rate and drifted higher: about **0.00448% per 8h** at 16:30, **0.00506%** at 16:41, **0.00583%** at 17:25, **0.00597%** at 17:32, and **0.00674%** by 17:49. Longs were paying shorts a few tenths of a basis point per eight hours. That is below the 0.01% per 8h neighborhood that is the usual Binance baseline. Nobody was paying up to hold this, in either direction. Funding does not confirm a crowded-long wipeout, and it does not confirm a crowded-short squeeze. It is a slight, rising tailwind for anyone who did get short and stayed.

Over the full 16:00–17:49 ET window, taker buy volume was 6,912 BTC and taker sell volume was 6,846 BTC. **Net taker delta for the two hours is about +66 BTC.** The scary minutes are real, and they were offset inside the same two hours by the 16:23–16:25 buy program and the 16:46–16:47 buy program. The board’s CVD near −2,500 BTC is a **session** cumulative that was already negative before 16:30 (price 1,300 points under VWAP is the same fact in a different unit). This hour added a violent down-then-up inside a hole that had already been dug.

---

## 5. Trading-firm / prop-desk perspective

This is how a book typically behaves in this window, held up against what this tape actually did. It is not a recommendation to copy it.

**Why this clock.** Cash equities are done at 16:00 ET. Index hedges, MOC imbalances, and the ETF create/redeem rush have printed. What is left, until 17:00 ET, is CME Bitcoin (still live) plus the offshore perp. After 17:00 ET the listed future is shut and the Binance perp is the liquid instrument. A desk that wants to change crypto delta without fighting the cash close waits until after 16:00. A desk that still wants a listed hedge available does the trade before 17:00. The 16:41 sweep sits in that slot: 41 minutes after the cash close, 19 minutes before the CME halt. The 17:26 sweep sits **after** the halt, in a perp-only book. Those are different liquidity regimes, and the prints look different. The pre-halt trade was four times the size and moved the level. The post-halt trade was a single minute of size into a one-tick coil and did not stick in the price.

**Why wait for a bid pocket.** Hitting a thin book moves the market against the seller and advertises the order. Hitting a displayed bid transfers inventory to someone who has already said they want it, at a price the seller can see. Implementation shortfall, for a seller, is better when the contra size is already lit. The cost of waiting is that the bid can be pulled, or can be a quote that was never meant to trade. The eleven minutes from the 16:30 still to the 16:41 sweep is the wait. The 17:20–17:25 coil, six minutes of a one-tick market with a +40M depth delta, is the same decision in miniature, and 17:25 is the minute the bid proved it would actually trade (46 BTC of sells, no price movement).

**Adverse selection on that choice.** The seller who hits a lit bid is selected against whenever the bid was lit **because** the buyer knows something, and the seller is selected for whenever the bid was lit by a market maker who will hedge and has no view. This tape cannot see the buyer’s motive. It can see the outcome. At 16:30 the bid was good: sellers hit it and price closed up. At 16:41 the bid was either smaller than the order or it stepped away after the first slice: price ran 141 points. A desk that sold the 16:41 sweep got filled, and then watched 16:46–16:47 lift the market ~180 points off the low while OI rose. That is the adverse-selection bill, paid in the half hour after the fill. It was not a wipeout — VWAP was still 1,300 points overhead, and the weekly open was only just reclaimed — and it was not free.

**TWAP and VWAP versus a sweep.** A VWAP seller is active all session, leaning into 85,740, not initiating at 84,300. A clock TWAP drips. The signature here is three separate one-minute imbalances, each above 80% taker sell, with quiet minutes in between:

- 16:27, 440 BTC, 83% sell, about −$24M net
- 16:41, 1,537 BTC, 95% sell, about −$116M net
- 17:26, 382 BTC, 94% sell, about −$28M net

That is liquidity-seeking behavior: wait, take the size when it is there, stop. It can be a discretionary trader or an implementation-shortfall algo with a participation cap. It is a poor match for a schedule that has to finish a fixed quantity by a fixed clock regardless of the book. The buy side of the hour has the same shape (16:24 at 669 BTC and +299 delta; 16:46 at 755 BTC and +601 delta). The hour is a sequence of sweeps in both directions, not a grind.

**Market maker absorption versus a directional buyer on the other side.** Absorption is what 16:30 and 17:25 look like: the aggressive sell trades, the passive bid prints, price does not break, and on 16:30 OI rises because both sides can be opening. A directional buyer looks the same in the prints until the next minute. The way this tape separates them is what happened when the next, larger sell arrived. At 16:41 the passive bid did not keep the price. A pure market-maker bid that was still there would have continued to lift, or the book-depth number would have stayed large. The depth panel is materially thinner after the candle, and the price is 200 points lower. So whatever was bidding at 16:30 did not absorb 16:41. The 16:46 buyer is easier to classify, because OI rose with the aggressive buy: someone paid up and **opened**. That can still be a market maker covering a short inventory from 16:41, except a cover reduces OI and OI rose by 800 BTC. The bounce buyer was adding length, not just repairing a short hat.

**Inventory after the fill, and the sticky short.** A short that is opened into a breakdown and then immediately covered shows up as OI given back on the first bounce. That give-back is missing. OI at the post-sweep shelf (about 97,660 at 16:43–16:45) went to 98,454 by 16:47 and to about 98,930 by 17:00. From there it leaked, and after 17:26 it leaked a bit faster, and at 17:49 it was still near 98,580. The 16:41 short, as a population, was still in the open interest when price traded 84,524 at 17:41.

The risk that population wears is a bounce that does not ask them to cover. Price can travel back through their fills (it did, by 17:00, and again to a marginal new high after the stills) while OI stays up, because the other side of the bounce was a new long rather than their own buyback. They are then short a market that is off the low, under VWAP, and held by a new long who has not had to mark a loss yet. The long’s risk is the mirror: the short inventory is still there, the depth cushion is thinner than it was at 16:30, and a second 16:41-type minute has a weaker book to land in. 17:26 was an attempt at that second minute. It did not recruit a new 967 BTC of OI, and the price came back. That is evidence the second attempt was a different flow, smaller and less committed, not evidence the first short has left.

**Perp versus spot, as a desk choice.** Selling the perp when it is already **$25–45 cheap to spot** is not a basis trade. A basis short sells the rich leg. Here the cheap leg was the one that got hit, and the discount widened at the low (about $26 at 16:30, about $43 at the 16:43 low, about $40 on the 17:26 low). The seller accepted a worse basis to get the perp filled. That is a directional perp position, or a hedge against something that is not Binance spot. CME was still open at 16:41, so a listed hedge was available for that sweep and was not available for the 17:26 one. This read cannot see the CME book. It can see that Binance spot was not the contra.

---

## 6. What looks intentional versus mechanical

**Looks like a decision to take displayed size.**

- A lit bid (depth delta +95M, yellow bands, two-sided footprint, unfinished auction) at 16:30, then ten quiet minutes, then one minute that is 95% taker sell.
- A lit bid at 84,450.80 that absorbs a 95% sell minute without moving (17:25), then the next minute 94% taker sell and a $58 trip.
- The same pattern on the buy side at 16:24 and 16:46. The hour is punctuated, not dripped.
- The perp trades the size and spot does not. That is a venue choice. Mechanical cross-exchange arbitrage would have pulled spot along within a dollar or two. Spot stayed ~$40 away and traded ~2% of the perp’s volume on the climax minutes.

**Looks like a position being opened, not a stop being run.**

- OI up 967 BTC on the climax sell, up 239 BTC on the earlier 16:27–16:29 sell.
- Forced sell liquidations of 2.4 BTC across two hours, against roughly 1,450 BTC of taker selling in a single minute.
- The low at 84,188.80 did not cascade into a second and third minute of rising volume. 16:42 was 89 BTC. The break stopped.

**Looks mechanical, or at least not a single human click.**

- 1,537 BTC in one minute is a workflow: a taker algo, a basket, a desk button that hands the slice to an execution tool. A single discretionary click can start it. The print itself is a program once it is in the matching engine.
- The 16:23–16:26 buy program and the 16:41 sell program have the same shape (one or two heavy minutes, OI rising, then silence). They may be one inventory flipping from long to short, or two books. The tape does not carry an account id, and this note does not invent one. What it does say is that the sell did not need a liquidation engine to happen.

**The 17:26 clip is the mixed one.** It has the intentional shape (wait for the one-tick bid, then hit it in one minute, perp only, spot absent). It does not have the open-interest signature of the 16:41 open. A program that is reducing length, and a program that is adding a small short on top of closing longs, produce this exact print. The board’s −25M box records the aggression. The OI column records that the position of the whole market barely changed.

**Quote, then fill, as a spoof test.** A spoof is size that is shown in order to move a price and is cancelled when the market comes to trade it. The 16:41 minute traded 1,537 BTC. The shown bid did not vanish in front of an empty print. Some of it, or something that replaced it, filled. A spoof can still have been layered behind a real bid, or pulled at the margin while the real bid traded. The still and the public aggregates cannot separate those. The honest statement is that the quote was followed by a real trade that broke the level, and the residual book an hour later was thinner.

---

## 7. Falsifiers

Each line is a check that would retire the fresh-short read of the 16:41 sweep. None of them printed, except where noted as a live residual risk.

1. **Open interest falls on the sweep minute.** A long liquidation, a long stop, or a short cover into a bid all reduce OI or leave it flat. OI rose 967 BTC. This check retires the “it was only longs getting out” reading. It does not retire the narrower point that **part** of the 1,455 BTC sell was longs getting out, because the sell was bigger than the OI change.
2. **The liquidation feed lights up.** A cascade of forced long closes would show sell-side liquidation volume on the same minutes as the taker sell. The feed shows 0.30 BTC at 16:41 and 2.02 BTC at 16:43. Retired for this window.
3. **Spot trades the size.** A cash seller, or a perp sell that is the hedge of a spot buy, shows comparable coin on BTCUSDT spot. Spot traded 31 BTC and 29 BTC on the two climax minutes, against 1,537 and 440 on the perp. Retired.
4. **The perp was the rich leg.** A basis short sells premium. The perp was $25–45 cheap to spot and got cheaper at the low. Retired as a basis trade. Still open as a hedge of some other instrument, including CME, which this note did not read.
5. **OI round-trips on the bounce.** If the 967 BTC came back out at 16:46–16:47, the short was a scalp and “sticky” is the wrong word. OI rose a further ~800 BTC on that bounce. The sticky-short description stands for the population. It does not stand for every account: individual shorts can have covered against new longs one-for-one, which is invisible inside a rising aggregate.
6. **The 16:30 footprint was the sweep.** If the heavy two-sided cells at 84,300–84,310 were themselves the one-sided climax, the “shown, then later consumed” sequence would collapse into one bar. They are two-sided, the bar closed up, and the climax volume is on a different minute whose low (84,249.8) is not even on that ladder. The sequence stands.
7. **The −25M box is the same trade as 16:41.** It is not. Different board, different price (84,450 versus 84,250), different hour, and the public minute that matches the later box added 67 BTC of OI rather than 967. Treating 17:26 as confirmation of the same fresh-short wave is the check that **fails in the other direction**: the later bar is real selling and a weak OI confirmation.
8. **Funding or a position transfer across the weekly open does the work.** Funding moved less than 0.002 percentage points per 8h. There is no expiry, no roll, no contract switch inside BTCUSDT perp on a Friday afternoon. Retired.
9. **The crosshair match is a coincidence and the tape is a different instrument.** The 16:30 bar matches open, high, low, close, and volume to the cent (84,310.20 / 84,332.40 / 84,300.00 / 84,332.40 / 379.67). The 17:25 bar matches the same way (84,450.90 / 84,450.90 / 84,450.80 / 84,450.80 / 48.65). Both OI bars match to the hundredth of a bitcoin. The instrument is the Binance USDT-M perp.

The residual that is still open, and that a later print could still use to revise the read: the passive counterparty at 16:41 is not identified, and any single account may have been flat by 17:00 inside an aggregate that stayed elevated. Account-level data would retire or confirm that. It is not in these stills.

---

## 8. Live watchlist next

Observational checks only. Nothing here is an order.

**Open interest, sticky versus bleed.** The levels that matter, in coin, from this window:

| Shelf | OI (BTC) | What it would mean if traded through |
| --- | --- | --- |
| Post-17:26 / right edge of the stills | ~98,800, tag **98.8K** | A bleed that stops here is the 17:26 seller covering and nothing else |
| Post-sweep shelf, 16:43–16:45 | ~97,660 | Giving this back means the 16:41 population is actually leaving |
| Pre-sweep, 16:40 | ~96,650 | Back here, the whole breakdown-add is gone |
| 16:30 crosshair | ~96,530 | Same neighborhood |
| 16:00 ET | ~95,555 | The hour’s entire build is gone |

As of 17:49 ET, OI was 98,583, a small bleed off the 98,931 peak and still far above the 97,660 shelf. The sticky side of the watch was the one printing at the time the stills were taken. A later break of 97,660 with price **rising** is the cover. A break of 97,660 with price **falling** is longs from the 16:46 bounce giving up, which is a different trade and would finally look like the liquidation mix the early read expected — if, and only if, the liquidation feed agrees. This window’s feed did not.

**CVD.** Board readings to beat or to hold: **−2,416 BTC** at 16:30, **−2,568 BTC** at 17:25, series tag **−2.9K**. Stabilizing means the line stops making lows under that −2.9K tag and the next heavy minute is not another 90%+ taker-sell bar. The two-hour net of about +66 BTC says the hole is older than this window. A CVD repair that only gets back to −2,400 has not undone the session. It has undone this hour’s dip.

**The bid.** The 16:30 cushion was a +95M depth delta and a yellow stack at 84,300–84,360 that did not survive 16:41. The 17:25 cushion was +40M at 84,450 and survived one minute (the doji) and not the next. A rebuilt bid that matters is a depth delta back toward the +80M to +95M area **and** a yellow band that stays lit while a large taker-sell minute fails to break it, the way 16:30 and 17:25 failed to break and 16:41 and 17:26 did not. Price location of that band is the whole question: a new band under 84,189 is defense of the low; a new band at 84,430–84,450 is defense of the weekly open and of the coil the −25M trade hit.

**Weekly open, 84,433.** Both captures printed live price just underneath it (84,403 and 84,404), with the 17:29 low at 84,389.50 and the board 2 high at 84,475.50. Reclaim, for this brief, means a series of closes back above 84,433 that do not depend on a single squeeze minute. The tape after the stills did trade 84,524 at 17:41 and was back at 84,471 by 17:49, so the level was already being fought in the minutes after the screenshots. VWAP at 85,700 is a different distance: more than 1,200 points. A reclaim of the weekly open is a local fact. A reclaim of VWAP is a session fact, and this hour did not attempt it.

**The low.** 84,188.80 is the printed low. It was made on a −117 BTC minute that followed the real sweep, with 2 BTC of long liquidations. A revisit that arrives with OI falling and with a liquidation print measured in hundreds of BTC would be the cascade this window did not have. A revisit that arrives with OI rising and with spot again absent would be the same short adding.

**Spot as the control.** On any follow-up sweep, spot volume and the perp–spot gap are the check. This window’s signature was a perp discount that widened toward **$40** while spot volume stayed near 30 BTC. If the next one prints on both books together, the “perp short, not cash seller” description stops applying.

---

## 9. Confidence and limits

**What is firm.**

- The boards are the Binance USDT-M BTCUSDT perpetual. Two crosshair bars match the public 1-minute candle on open, high, low, close, and volume. Both crosshair OI bars match to the hundredth of a coin. The low tag 84,188.80 matches the 16:43 low of 84,188.8. The board 2 high tag 84,475.50 matches the 17:18 high. The board 2 low tag 84,389.50 matches the 17:29 low.
- The 16:41 minute is a one-sided taker sell of about 1,455 BTC against 82 BTC of taker buys, with OI up 967 BTC and long liquidations of 0.30 BTC.
- The 17:26 minute is a one-sided taker sell of about 358 BTC against 24 BTC, with OI up 67 BTC and no meaningful liquidation, and it is the minute that sits in the same magnitude band as the highlighted −25M box.
- Spot did not participate in size. The perp traded at a discount to spot throughout, and the discount widened on the sells.
- Forced liquidations across 16:00–17:49 ET are under 4 BTC combined, both sides.

**What is soft.**

- Delta-box glyphs other than the ones listed in the appendix were read from a wide, dark chart. The big ones (−25M, −23M, −21M, −18M, −12M, −13M, −8M, −6M, −5M, −4M, and the 4M–7M greens) were checked on tight crops. Smaller K labels are a field, not an audited ledger. Vertical stacks are not a minute-by-minute sequence.
- Footprint column order is not labeled. The unfinished-auction flag, the cell numbers, and the tooltip arithmetic are on the still. Which column is the bid is inferred from how these ladders usually work and from the two-sided totals, and that inference is marked as such wherever it is used.
- The tooltip’s 667K × 5.20M is a platform bucket. It is not independently rebuilt from order-book snapshots. Historical depth is taken from the panel the operator shot (+94.86M, +40.31M, and the ~30M right-edge tags). No second source reconstructed the book.
- USD notionals are coin delta times the minute close. They are there so a −1,372 BTC print can be compared with a −25M box. They are not Binance’s official quote delta.
- CVD on the board is a session cumulative whose zero point is the platform’s, not this note’s. The two-hour net of +66 BTC is computed from scratch over 16:00–17:49 ET and is not expected to equal −2,416.
- The trough of the CVD line during 16:41–16:43 is drawn and is not numbered. The numbered CVD prints are −2,416.51, −2,567.96, and the −2.9K tag.
- No account, no desk, no beneficial owner. “A short” in this note means net new short exposure in the aggregate. Many accounts can sit inside that aggregate on both sides.
- CME’s own book was not pulled. The halt time is the standard Friday 16:00 America/Chicago close, and it agrees with the footer (“CME opens 2d” at 17:29 and at 17:32). It is context, not a print on this chart.

**Paper.** Nothing in this note is an instruction to buy, sell, or size a position. The watchlist is a list of measurements that would confirm or retire the read.

---

## Appendix A — what was transcribed off the stills

**Board 1 header.** BTCUSDT, Bitcoin, 1m. O 84310.20 H 84332.40 L 84300.00 C 84332.40 +22.20 (+0.03%). Vol 379.67. VWAP 85740.86. Weekly Open 84433.00. Live 84403.30. Bell 84303.96. Low 84188.80. Axis grids include 84480, 84440, 84420, 84380, 84360, 84340, 84320, 84280, 84260, 84240, 84220, 84200, 84160.

**Board 1 OI strip.** O 96369.78 H 96533.94 L 96369.78 C 96529.40. Right tag **b 98.8K**, with 98.0K / 97.0K / 96.0K grid. The subplot is a line that steps up, plus a histogram of small teal and red ticks and one taller teal block in the middle of the view, i.e. on the sell/bounce portion rather than on the 16:30 crosshair.

**Board 1 CVD.** “CVD BTC −2416.51”. Line flat, then a clear drop, then a partial recovery that stays below the 16:30 level. Grid label −2.4K. Series tag binance.f −2.9K.

**Board 1 depth.** “Order Book Depth 0–5% Delta: 94.86M”. Histogram elevated, then lower. Right edge 30.39M.

**Board 1 footer.** Fri, 02 Oct 2026 16:30:00, “1h 2m ago”, axis mark 16:45. Chat. Trade balance in 3d 14h. CME opens 2d. UTC−4 17:32:17. 128 ms.

**Board 1 delta boxes confirmed on tight crops.** −23M, −21M, −18M, −13M, −12M, −8M, −6M, −5M, −4M, −3M, and several −2M. Also −839K, −822K, −766K, 985K, 609K, 607K, and greens 7M, 6M, 6M, 5M, 5M, 4M, 4M. The wider field also shows, with lower confidence on the exact glyph: 993K, 1M, −2M, −210K, 2M, 951K, 517K, 3M, −345K, −410K, −1M, −298K, 984K, 914K, −1M, 1M, 202K, 709K, −415K, −328K, −177K, −10M, −805K, −570K, −863K, −264K, −50K, 633K, 12K, 602K, −265K, −684K, −201K, 432K, 100K, 93K, −395K, −112K, −80K, −425K, 858K, 526K, 104K, 228K, −245K, −51K, −30K, 516K, 982K, 458K. Left-edge partials (849K, −146K, −278K) are cut off by the frame.

**Board 2 header.** BTCUSDT, Bitcoin, 1m. Calls widget **OFF** (UI state, not a market print). O 84450.90 H 84450.90 L 84450.80 C 84450.80 −0.10 (−0.00%). Vol 48.65. VWAP 85699.91. Weekly Open 84433.00. High 84475.50. Bell 84446.72. Live 84404.10. Low 84389.50. OI tag b 98.8K.

**Board 2 OI.** O 98784.26 H 98798.22 L 98784.16 C 98797.92. The line on this zoom is flat at the top of a 95.0K–98.8K scale, with tiny teal and red ticks.

**Board 2 CVD.** −2567.96. Gentle downward drift. −2.4K grid. binance.f −2.9K.

**Board 2 depth.** Delta 40.31M. Right edge 29.85M. A 50.00M grid mark is on the axis.

**Board 2 footer.** Fri, 02 Oct 2026 17:25:00, “4m 47s ago”, axis mark 17:30. Trade balance in 3d 15h. CME opens 2d. UTC−4 17:29:47. 133 ms.

**Board 2 delta row, left to right, high confidence.** 254K green, −577K, −381K, −1M, −719K, 748K green, −2M, −4M, −25M. The last two are inside the operator’s white box. Lower cluster: −495K, −828K, 465K, 375K, 476K, 203K, 438K, plus −557K, −247K, −525K, −2M, 1M on the red candle, and a wick mark at 84389.50. Partial labels cut off at the left frame (a green box ending in M, and figures near 677K / −983K) are not used.

## Appendix B — sources

- Stills: the two desk screenshots of 2 Oct 2026, read directly and by magnified crop. Glyphs that were checked on a crop are listed above; the rest of the small labels are flagged as lower confidence.
- Binance USDT-M BTCUSDT perpetual, 1-minute candles, taker buy, taker sell, open interest, liquidations, and funding, 2026-10-02 20:00Z to about 21:50Z. Category PERPETUAL, symbol BTCUSDT.
- Binance spot BTCUSDT 1-minute candles for the same window, used only as the control in sections 2, 5, and 7.
- CME timing is the ordinary Friday halt (16:00 America/Chicago) and is corroborated by the chart footer, not by a CME print.

USD figures in the tables equal (taker buy BTC − taker sell BTC) × that minute’s perp close. Coin figures are the exact aggregates.
