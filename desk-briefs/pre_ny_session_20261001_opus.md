# Pre-NY Session Brief: BTC, Thu 1 Oct 2026

**Paper only.** This is analysis documentation, not a trade instruction. No orders, no live size.

| | |
|---|---|
| Written | ~15:20 Europe/Budapest (CEST) = ~13:20 UTC = ~09:20 America/New_York |
| Chart snapshots | TradingView 09:16 ET, OpenMarket 09:13 ET, MMT 15m bar stamped 09:00 ET (about 09:12) |
| Spot reference | ~83,48x (TradingView BTCUSDT.P 83,487.7; OpenMarket 83,484.0; MMT aggregated spot 83,562 a few minutes earlier) |
| Instruments | Binance BTCUSDT perp (TradingView, OpenMarket right pane), Binance spot (OpenMarket left pane), MMT 7-venue aggregated spot |

---

## The call

**Lean bearish into the open, but expect support underneath rather than a trend day.** BTC lost the
**Monthly / Quarterly / Daily Open at 83,577** about 40 minutes before the NY cash open. On the way
down it broke through the 83.6–83.76k cluster (Daily initial-balance high, session VWAP, weekly VWAP,
Monday mid). Perp open interest *rose* while perp and Binance-spot CVD fell, which means new shorts were
opening on the break. Positions were not being closed.
On the macro side, yesterday's "cool" PCE has already been tested and faded. Ten-year yields are at
2002 highs, and claims were firm again this morning. Nothing on the macro side is pulling against the
sellers until rates turn.

- **Base case (~45%): accept below the monthly open and probe lower.** Price rotates down into
  83,370 (initial-balance low) and 83,320 (NY low), and possibly the 83,137 day low, where book bids are
  stacked. After that, expect chop between 83.1k and 83.6k into NFP.
- **Bull case (~30%): defend and reclaim, leading to a short squeeze.** A fast reclaim of 83,577–83,613
  traps the shorts who just opened. Targets are 83.72k (VWAP), 83.9k (NY VWAP), and 84.0–84.1k (4h POC).
  Above that, about 300 BTC of aggregated spot offers sit at 84.4k.
- **Bear tail (~25%): bids are pulled and price breaks down.** This one needs a hot ISM prices-paid print
  or a new high in the 10Y above 5.342%. It runs 83,137, then 82,900 (previous-day low), then 82,570
  (Monday low).

The monthly open decides which case is live. Below 83,577, sellers control the day. If price gets back
above 83,613 and holds, shorts are offside and the bull case is on.

---

## 1. Macro state into NY

### 1a. PCE: cooler headline, discounted by the market

What printed on Wed 30 Sep (August PCE, released with BEA's annual revision):

- **Core PCE** came in at 3.0% y/y against a 3.3% estimate, and 0.2% m/m (0.247% unrounded) against
  0.3%. **Headline** was 3.4% y/y against 3.7%.
- **July was revised down by the same amount.** Core went from 3.3% to 3.0% and headline from 3.7% to
  3.4%. So August's core y/y was flat against the revised July. Unrounded, it actually ticked up slightly.
- **Methodology change.** BEA changed how it measures three items: portfolio management and investment
  advice (now uses an employment-based quantity measure instead of deflating by the PPI), computer
  software (new composite deflator), and legal services (an unpublished CPI series was replaced after it
  became "unusually volatile"). The macro clip (image 4) estimates this alone takes up to about 20bp off
  core. RBC had estimated about 18bp; the actual revision to July was about 30bp.

How the market received it (images 4–6):

- **Rates refused the good news.** Per image 5, Treasury yields "erased all losses and turned green."
  10Y was at 5.294% (+3.4bp) and 30Y at 5.641% (+4.7bp), while 2Y was at 4.885% (−0.4bp). The front end
  took the cooler print; the long end sold off anyway.
- **This morning the 10Y extended.** It hit **5.342%** (Reuters, 08:14 UTC), the highest since early
  2002. The 30Y hit about **5.67%**, the highest since July 2002 (CNBC). Image 6 shows the 10Y up
  **+55bp in September** and +138bp from the March 2026 low, with mortgages near 7.60%.
- **BTC already ran the "cool PCE" trade and gave it back.** It popped to the previous-day high of
  **85,632.70** (OpenMarket) and is now ~83.48k, down about 2.5% from that high. CoinDesk's write-up
  says the same: "soft-inflation pop to $85,500 fades as bond yields refuse to fall."

**Discount thesis: confirmed.** Most of the "miss" was a change in measurement, and the Fed knows it.
The Fed hiked on 16 Sep to 3.75–4.00%, and 16 of 18 dots show another hike in 2026. Inflation momentum
did not slow on the new basis, so the PCE does not give the Fed a reason to stop. The rates market
agrees: if anyone believed in real disinflation, 10s and 30s would have rallied. Instead, the curve is
**bear-steepening**. Long-end yields are rising faster than short-end yields, so 2s10s is about +41bp and
2s30s about +76bp. That points to higher term premium (supply, oil, fiscal), not a shift in the Fed
path. Term-premium selloffs hit long-duration risk hardest: Nasdaq growth, and BTC as a high-beta
version of it.

**For crypto: treat the PCE as already priced, with a slightly bearish tilt.** The good-news rally
happened and failed. Fading good news is a weak-tape signal.

### 1b. Jobless claims (released 08:30 ET today)

| Series | Actual | Consensus | Prior |
|---|---|---|---|
| Initial claims, week ending 26 Sep | **197K** | 199K (ActionForex / nowflation); WSJ survey 200K; FXStreet 201K | 198K (revised up from 197K) |
| 4-week average | **200.0K** | ~199K | 202.5K (revised) |
| Continuing claims, week ending 19 Sep | **1.701M** (−11K) | 1.720M (nowflation) | ~1.712M |

- Initial claims were the lowest since mid-July (AP). Continuing claims were the lowest since 2023
  (Continuum).
- Claims beat consensus slightly, and continuing claims beat by more. Layoffs are low and job finding
  looks better. Nothing here argues against a December hike.
- **Transmission into the NY session: claims, then rates, then risk, then BTC beta.** A firm print keeps
  the front end from rallying (CNBC had the 2Y +2bp to ~4.91% earlier this morning). That leaves 10s and
  30s free to keep pushing new highs, which tightens conditions for equities, and BTC trades as high-beta
  Nasdaq. BTC's leg down from ~84.0k to 83.48k happened in the 08:30–09:15 ET window, right after the
  print. That timing fits the transmission chain, but I can't prove the print caused the move.

### 1c. Rates path and what it means for BTC into NY

| Tenor | Yesterday post-PCE (image 5) | This morning | Read |
|---|---|---|---|
| 2Y | 4.885% (−0.4bp) | ~4.91% (+2bp, CNBC pre-claims) | Front end firm; hike pricing intact |
| 10Y | 5.294% (+3.4bp) | high 5.342% (Reuters) | New 24-year high; 5.30% is now the pivot |
| 30Y | 5.641% (+4.7bp) | ~5.67% (CNBC) | Highest since Jul 2002 |

What the 10Y level means for BTC:

- **Above 5.34% (a new high):** the main risk-off trigger for BTC this session. It likely forces the bear
  tail.
- **Holding 5.28–5.34%:** BTC has no macro support, and the base case (probe lower, then range) holds.
- **Back below ~5.28%:** the only macro path that supports the bull case. CoinDesk's framing applies: "A
  sustained drop in that yield is the move that would give the next rally room to hold."

### 1d. Calendar risk (ET)

| Time | Event | Consensus | Note |
|---|---|---|---|
| 09:30 | US cash equity open | n/a | OpenMarket footer at 09:13 ET read "NY opens 17m" |
| 09:45 | S&P Global US Mfg PMI (final, Sep) | 57.0 (flash 57.0) | Low impact unless revised hard |
| **10:00** | **ISM Manufacturing (Sep)** | 54.8 (nowflation) / 54.9 (WSJ); prior 54.6 | **Main intraday catalyst.** Prices paid matters more than the headline: Continuum previews 72.5 vs 71.1 prior. A hot prices-paid print would push the 10Y to a new high, which feeds the bear tail. |
| 10:00 | Construction spending (Aug) | +0.1% | Low impact |
| 12:00 | Binance perp funding | +0.0053% at snapshot | OpenMarket countdown read 02:46:06 at 09:13:53 ET. Funding is flat, so shorts are not yet crowded. |
| After close | US spot BTC ETF flows | n/a | 30 Sep printed −$148.7M (FBTC −$125.6M, IBIT −$9.5M), ending a 9-day, ~$3B inflow streak. Treat that figure as possibly preliminary. |
| **Fri 08:30** | **September NFP** | +84K (WSJ) / +100K (nowflation); UR 4.1–4.2%; AHE +0.3% m/m; prior +162K | OpenMarket shows **"NFP in 23h 16m"** at 09:13 ET. Expect afternoon range compression and de-risking into the print. |

---

## 2. Level map (native TradingView as the spine)

Prices are read from the screenshots and are approximate. Weekly opens differ by about 20 points
between venues (TradingView 84,412.6, OpenMarket 84,433.0). Readings marked with "?" are uncertain.

| Price | Level | Source | Role now |
|---|---|---|---|
| ~87,650 ? | **Yearly open** (dashed teal) | TV 4h | Upper HTF rail, not in play today |
| ~87,350–87,396 | Previous-week high (visible-range high 87,395.67) | TV 4h | HTF resistance |
| 85,632.70 | **Previous-day high** (PCE pop) | OpenMarket | The failed good-news high |
| 85,000 | Monday high / 85k round number | TV 4h | Weekly balance top |
| ~85,130 | 4h volume-profile value-area high | TV 4h | Top of the two-week balance |
| **84,380–84,450** | **Daily high 84,379.80 + Weekly Open 84,413–84,433 + ~300 BTC aggregated offers** | OpenMarket, TV, MMT | **Hard ceiling for NY.** Three separate signals at one price. |
| ~84,195–84,215 | Upper session-VWAP band | TV 5m tags | First stretch target in a squeeze |
| **~84,000–84,120** | **4h POC (~84.0k), previous 4h high (~84.05–84.12k), week-to-date mid (~84.1k), previous-week mid (~84.1k)** | TV 4h/5m, derived | **Value magnet.** Price below the POC = sellers lead in the balance. |
| ~83,960 | ORL (gray; unclear which opening range) | TV 5m | Minor |
| ~83,897 | **NY VWAP** | TV 5m | Bull case second target |
| ~83,850 | 4H open | TV 5m | Minor |
| **~83,690–83,760** | **Operator's LTF confluence: session VWAP 83,716–83,720 (MMT daily VWAP 83,715.63), weekly VWAP ~83,690, Monday mid ~83,730–83,760** | TV 5m (annotated), MMT | **Pivot band.** Holding above it would make the bull case real. |
| 83,600–83,613 | **Daily initial-balance high** (IBH 83,612.6; green line 83,600.1) | TV 5m | Reclaim trigger |
| **83,576.8–83,577** | **MONTHLY OPEN = QUARTERLY OPEN = DAILY OPEN** (1 Oct 00:00 UTC) | TV 5m/4h, OpenMarket | **The decision level.** The shorting trigger fired off it (image 2). Q4's first test is happening on day one. |
| ~83,500–83,550 ? | Rising 4h green line (looks like an anchored VWAP or MA) | TV 4h | Price is sitting on it. A 4h close below adds weight to the bear side. |
| 83,491.3 | Initial-balance midpoint | TV 5m | **Price is here at snapshot.** |
| 83,370 | **Initial-balance low** (red line) | TV 5m | Base case first target |
| ~83,320 | NY low (yesterday's NY session) | TV 5m | Base case second target |
| ~83,190 | Lower session-VWAP band | TV 5m | Stretch |
| 83,136.6 | **Day low / previous 4h low** | OpenMarket, TV | Base case extension and bear-tail trigger |
| ~83,000–83,050 | Large resting bids (MMT ~191 BTC at ~83.0k; Binance spot ladder clusters 82.95–83.06k) | MMT, OpenMarket | Book floor |
| 82,901–82,920 | **Previous-day low** | OpenMarket (82,901.30), TV | Bear tail first target |
| ~82,870 | 4h value-area low | TV 4h | Losing it would break the two-week balance |
| ~82,570 | **Monday low** | TV 4h | Bear tail second target, weekly low |
| ~80,850 | Previous-week low | TV 4h | HTF; not today absent a shock |

**Structure in one line.** BTC is in a two-week balance (value area roughly 82.87k–85.13k, POC ~84.0k).
Price sits in the lower half, below the POC and below the triple open. Sellers have the edge in the
balance, but the value-area low and previous-day low are ~600 points away, and that space is full of
resting bids.

---

## 3. Order flow and books

### 3a. Binance spot vs perp: who is selling?

Annotations from image 2: "Taker selling on Binance spot" on the spot CVD pane, and "Some shorting
trigger off the monthly open level" boxed on the perp OI and CVD panes.

- **Binance spot CVD** rolls from about −0.95K to **−1.17K BTC** from ~05:00 to ~09:10 ET. Spot takers
  are hitting bids, so this is real spot supply, not just perp leverage.
- **Binance perp CVD** drops from about 0 to **−749 BTC** inside the boxed window (~08:30–09:15 ET).
- **Binance perp open interest rises in the same window:** 95,728 → 95,848 BTC (high 95,848.09), about
  +120 BTC, ticking higher into the snapshot.

**This was shorting, not long liquidation.** The setup brief described an "OI flush + CVD drop," but
the chart doesn't show a flush. OI went *up*.

- In a long liquidation, aggressive selling comes with *falling* OI, because forced sellers are closing
  positions.
- Here, aggressive perp selling came with *rising* OI, which means new short positions were opening.
  Shorts sold the break of the monthly open, exactly as the operator flagged.
- Spot taker selling alongside it means the move had real spot sellers, not just perp leverage.

**Why it matters.** These new shorts have a short history and a known location: entries around
83.5–83.6k, right at the monthly open. Funding is only +0.0053%, so they aren't paying to hold yet.

- If price accepts lower, they are right and add pressure.
- If price reclaims 83,577–83,613, they are offside within points of entry, and short covering becomes
  the fuel for the bull case.
- The tell is OI: price up with OI falling means short covering (squeeze); price down with OI rising
  means continuation.

### 3b. MMT aggregated spot (7 venues), image 3

Annotation: **"Nearly 300 BTC offers quoted at daily high on spot exchanges (aggr)."**

- **The ceiling.** The boxed heatmap bands sit at about **84.39–84.45k**. The tooltip rows read about
  75 and about 115 BTC per level, and the OB profile shows more size stacked at 84.4–84.5k. That
  matches the daily high (84,379.80) and the weekly open (84,413–84,433). A squeeze should stall there
  unless the offers are pulled or lifted. **Pulled offers would be the bullish tell. Offers that refill
  as they get lifted mean a seller is defending the weekly open.**
- **Nearer asks** stack at 83.6–83.8k (about 152, 137, 101 BTC), which overlaps the VWAP and initial-
  balance cluster. Squeeze attempts hit passive supply right away.
- **Bids underneath:**

| Price | Aggregated bid |
|---|---|
| ~83,530 | ~188 BTC |
| ~83,400 | ~134 BTC |
| ~83,200 | ~92 BTC |
| **~83,000** | **~191.5 BTC (largest)** |

- **Aggregated spot CVD** rose from about −6.0K to about −4.6K through the Asia and early-London
  session (spot dip-buying after the 04:00 ET low). It is now rolling over to **−4.90K**, and delta
  volume printed −24 on the current bar. The spot bid that carried the morning bounce has stepped back.

### 3c. Book depth into the open

| Measure | Reading | Read |
|---|---|---|
| Binance spot 0–5% depth delta | +37.61M (jumped on the last bars) | Bid-heavy |
| Binance perp 0–5% depth delta | +150.25M | Bid-heavy, steady |
| MMT aggregated 2.5% depth | +0.179 (uptick on the last bar) | Modestly bid-skewed |

**Bias:** passive bids sit below while aggressive sellers hit them. That divergence resolves one of two
ways:

1. **Absorption.** CVD keeps falling but price stops making new lows above 83.37k / 83.32k. Bids are
   eating supply, and that sets up the squeeze.
2. **Pull.** Depth delta collapses (bids pulled), and price slides through 83.37k → 83.14k → 83.0k
   with little resistance.

Passive depth can be pulled; trades can't be undone. I weight the CVD and OI evidence above the depth
deltas, which is why the lean is bearish despite bid-heavy books.

### 3d. Cross-check: rejection of the monthly open, or a squeeze setup?

**Right now, flow confirms a rejection.** All four signals agree:

- spot takers are selling (Binance and aggregated spot CVD both rolling over)
- perp shorts are adding (OI up, CVD down)
- price is below 83,577 and below every VWAP
- the morning's spot bid has faded

**The squeeze setup exists but hasn't triggered.** Its ingredients are fresh shorts at a known level,
flat funding, and bid-heavy depth. It needs a trigger: a reclaim of 83,613 with OI falling, ideally
with a US spot bid (watch the Coinbase_IBIT tab) and the 10Y backing off 5.30%.

---

## 4. Confluence synthesis (levels × flow × macro)

**The story.** The market tested "good news" yesterday (cool PCE), and good news failed. BTC went to
85.6k and came all the way back, because the PCE beat was mostly a measurement change and the long end
kept selling off. This morning, firm claims and a new 24-year high in the 10Y removed the macro support.
At the same time, BTC broke the most important level on the chart: the monthly, quarterly, and daily
open at 83,577. Spot takers sold and perp shorts opened. The market is now in the lower half of a
two-week balance, below the 4h POC, and sitting on stacked bids. Into a Friday NFP, the most likely
path is lower prices without a trend day.

### Scenario A (base, ~45%): accept below the monthly open and probe the initial-balance low and day lows

- **Path:** the cash open holds under 83,577 / 83,613. Price rotates into 83,370 (initial-balance low)
  and 83,320 (NY low). An extension tags 83,137 (day low) and the ~83.0k bid block. Bids absorb there,
  then price ranges 83.1–83.6k into the afternoon NFP compression.
- **Supporting evidence:** OI rising while CVD falls, spot CVD rolling over, price below all VWAPs, the
  10Y holding 5.30%+, firm claims, and the PCE fade.
- **Invalidation:** a 15m/30m close and hold back above **83,613** (initial-balance high), with perp OI
  falling (shorts covering). That switches to Scenario B.
- **Escalation to the bear tail:** a 15m close below **83,137** with depth delta collapsing.

### Scenario B (bull, ~30%): defend and reclaim, leading to a short squeeze

- **Path:** the open or the 10:00 ISM gives a spike low that holds above 83,320 / 83,137 (absorption).
  Price reclaims 83,577–83,613 quickly and traps the shorts that sold the monthly-open break. Squeeze
  targets are 83,72x (session VWAP / weekly VWAP / Monday mid), then 83,897 (NY VWAP), then
  84,000–84,120 (POC, previous 4h high, weekly mids).
- **Extension to 84,38x–84,45x** (daily high, weekly open, ~300 BTC offers) only if the 10Y breaks back
  below ~5.28% *and* the aggregated offers are pulled or lifted. Without both, plan for a stall at
  84.0–84.1k.
- **Required tells:** price up with OI down, spot CVD turning up (US / Coinbase bid), depth staying
  bid-heavy.
- **Invalidation:** rejection at the 83.69–83.76k VWAP cluster followed by loss of **83,491**
  (initial-balance mid). A 5m close back below **83,370** voids the case entirely and puts Scenario A
  back on.

### Scenario C (bear tail, ~25%): bids pulled and the breakdown runs

- **Trigger:** a hot ISM prices-paid print (above ~72.5) or a 10Y break above **5.342%**, followed by
  bids pulled at 83.0–83.15k.
- **Path:** 83,137 → 82,900 (previous-day low) → 82,870 (value-area low) → 82,570 (Monday low).
  Accepting below value opens the two-week balance to the downside for Friday.
- **Invalidation:** a failed breakdown, meaning a reclaim of **83,137**, then **83,370**. That puts the
  move back into the Scenario A range.

### How much weight the "cool PCE, but discounted" story gets for crypto

**Net zero to slightly bearish. Don't count it as support.**

- The bullish reading ("inflation is cooling, so the Fed is done") has already been priced and sold:
  85.6k back to 83.5k.
- The rates market rejected it: the long end set new highs after the print.
- The Fed has no reason to accept a measurement-driven miss as progress.

The only way PCE matters for BTC today is through the 10Y. If the long end finally rallies on
inflation relief, that supports the bull case. If it doesn't, the fade continues.

---

## 5. What NY will look at: checklist for 09:30–13:30 ET (paper only)

**Price**
- [ ] **09:30–10:00: monthly open 83,577.** Is it reclaimed or rejected? First 15–30m acceptance
  decides between Scenario A and Scenario B.
- [ ] 83,613 initial-balance high: the reclaim trigger. 83,491 initial-balance mid: where price sat at
  the snapshot.
- [ ] 83,370 initial-balance low and ~83,320 NY low: base case targets. Do they hold on the first test?
- [ ] 83,137 day low and the ~83.0k bid block: bear-tail trigger if they break with bids pulled.
- [ ] 83.69–83.76k VWAP cluster (session ~83,716, weekly ~83,690, Monday mid): the first wall in a
  squeeze.
- [ ] 84.0–84.12k POC / previous 4h high, then 84.38–84.45k daily high / weekly open / ~300 BTC offers:
  the squeeze ceilings.

**Macro and data**
- [ ] 10:00 ISM Manufacturing: headline vs 54.8–54.9, and **prices paid vs ~72.5**.
- [ ] **US 10Y vs 5.30% / 5.342%** (new high means risk-off) and **30Y vs 5.67%**. Does 2s10s keep
  bear-steepening?
- [ ] Nasdaq / NDX opening drive. BTC is trading as high-beta duration.
- [ ] Mortgage-rate and housing chatter (7.60% mortgages) as a sign that rate pain is spreading.
- [ ] NFP positioning: expect range compression after ~12:00 ET. Don't read afternoon chop as a signal.

**Flow**
- [ ] **Perp OI vs price:** price up with OI down means a short squeeze (Scenario B). Price down with
  OI up means continuation (Scenario A or C).
- [ ] Binance spot CVD and MMT aggregated spot CVD (−4.90K): do US-hours spot buyers show up? Check the
  Coinbase_IBIT tab for a US spot bid.
- [ ] ~300 BTC offers at 84.4k: pulled (bullish), refilled (defended), or lifted (breakout)?
- [ ] Depth deltas (Binance spot +37.6M, perp +150M, MMT 2.5% +0.179): do they hold or collapse on the
  first push lower? This separates absorption from a pull.
- [ ] 12:00 ET funding (+0.0053%): does it turn negative? Crowded shorts raise squeeze risk.
- [ ] After the close: the US spot ETF flow print. A second outflow day after −$148.7M would confirm
  that the institutional bid has paused.

---

## Image map

| # | Source | What it showed | Used in |
|---|---|---|---|
| 1 | TradingView BTCUSDT.P 5m + 4h | LTF confluence ~83.7k (session VWAP, weekly VWAP, IB), monthly/quarterly/daily open 83,577, NY VWAP, previous 4h/day levels, 4h POC ~84k, value area, yearly open, previous-week high/low | §2, §4, §5 |
| 2 | OpenMarket Binance spot + perps | "Taker selling on Binance spot"; "shorting trigger off the monthly open" (OI up, CVD down); depth deltas; daily high/low; previous-day high/low; NFP countdown; funding | §1d, §3a, §3c, §3d |
| 3 | MMT 7-venue spot, 15m | "~300 BTC offers at daily high (aggr)"; daily VWAP 83,715.63; aggregated book bids/asks; spot CVD −4.90K; 2.5% depth +0.179 | §2, §3b, §3c |
| 4 | Macro clip: PCE methodology | Three category changes, up to ~20bp off core, July −30bp; "measurement change" | §1a, §4 |
| 5 | Macro clip: yields post-PCE | Yields green on the day; 10Y 5.294%, 30Y 5.641%, 2Y 4.885% | §1a, §1c |
| 6 | Macro clip: 10Y > 5.30% | Highest since Apr 2002; +55bp in the month; +138bp from the March low; mortgages ~7.60% | §1a, §1c |

## Sources (accessed 1 Oct 2026)

- Jobless claims: [ActionForex, 1 Oct 2026](https://www.actionforex.com/live-comments/656069-us-jobless-claims-fall-to-197k-offering-no-sign-of-labor-weakness-ahead-of-nfp/) (197K vs 199K consensus; prior revised to 198K; 4-week average 200.0K). [FXStreet, 1 Oct 2026 12:37 GMT](https://www.fxstreet.com/news/us-initial-jobless-claims-dropped-to-197k-last-week-202610011237) (continuing claims 1.701M, −11K). [AP via The Independent, 1 Oct 2026](https://www.independent.co.uk/news/labor-department-washington-donald-trump-iran-covid-b3059765.html) (lowest since mid-July). [Continuum Economics, 1 Oct 2026 12:44 UTC](https://continuumeconomics.com/a/631c4119/us-initial-claims-remain-very-low-continued-claims-have-fallen-significantly) (continuing claims lowest since 2023).
- Calendar and consensus: [nowflation calendar](https://nowflation.com/calendar). [Dow Jones / WSJ survey via MarketScreener, 30 Sep 2026](https://www.marketscreener.com/news/unemployment-rate-expected-to-hold-steady-data-week-ahead-ce785ad2d08cf12c). [Kiplinger week ahead](https://www.kiplinger.com/investing/economy/this-weeks-economic-calendar). [Continuum ISM preview, 30 Sep 2026](https://continuumeconomics.com/a/da797eff/preview-due-october-1-us-september-ism-manufacturing-back-to-near-the-recent-high).
- PCE and methodology: [BEA annual update blog, 17 Aug 2026](https://www.bea.gov/news/blog/2026-08-17/annual-update-gdp-industry-and-state-stats-publicly-available-starting-sept-30). [BEA SCB preview, Jun 2026](https://apps.bea.gov/scb/issues/2026/06-june/0626-nea-preview.htm). [TheStreet Pro](https://pro.thestreet.com/market-commentary/core-inflation-moderates-while-real-spending-jumps). [Wolf Street, 30 Sep 2026](https://wolfstreet.com/2026/09/30/not-even-massive-changes-of-methodology-can-get-pce-inflation-back-into-the-bottle/).
- Rates: [Reuters, 1 Oct 2026 08:14 UTC](https://www.reuters.com/world/10-year-us-treasury-yield-hits-highest-since-2002-2026-10-01/). [CNBC, 1 Oct 2026](https://www.cnbc.com/2026/10/01/us-treasury-bond-yield.html).
- Fed: [FOMC statement, 16 Sep 2026](https://www.federalreserve.gov/monetarypolicy/files/monetary20260916a1.pdf). [CNBC Fed decision, 16 Sep 2026](https://www.cnbc.com/2026/09/16/fed-rate-decision-september-2026.html).
- BTC and ETF flows: [CoinDesk, 1 Oct 2026](https://www.coindesk.com/markets/2026/10/01/bitcoin-s-soft-inflation-pop-to-usd85-500-fades-as-bond-yields-refuse-to-fall). [Farside via Blockchain.News, 30 Sep 2026](https://blockchain.news/flashnews/bitcoin-etf-148-7m-net-outflow-sept-30). [Crypto Briefing, 30 Sep 2026](https://cryptobriefing.com/spot-bitcoin-etfs-3b-inflows-nine-days/).

---

## Executive summary

1. **Call:** lean bearish into NY. BTC lost the monthly/quarterly/daily open at **83,577**, and the base
   case is a probe of **83,370 / 83,320 / 83,137** into stacked bids, then range trading before NFP.
2. **Flow:** spot takers are selling and perp OI rose while CVD fell. New shorts opened at the monthly
   open; this was not a long flush.
3. **Ceiling:** about **300 BTC** of aggregated spot offers sit at **84.4k**, on the daily high and
   weekly open. Any squeeze likely stalls at the 84.0–84.1k POC or 84.4k.
4. **Macro:** the cool PCE is mostly a measurement change and has already been faded. Claims were firm
   (197K vs 199K) and the 10Y is at a 2002 high (5.34%). Only a 10Y move back below ~5.28% supports a
   rally.
5. **Flip level:** a hold above **83,613** with OI falling switches to the squeeze case (83.72k →
   83.9k → 84.0k). A loss of **83,137** with bids pulled opens **82.9k / 82.57k**. Paper only.
