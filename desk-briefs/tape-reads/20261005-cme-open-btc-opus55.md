# CME BTC futures open, 4 Oct 2026: paper tape read

Research only. This note describes what was on screen. It has no orders, no strategy, and no notional values.

## Coverage

**Coverage: the input was 1858 one-second frames from a proxy, not the original 50308 frames.**

- Original (not seen): `CME_open_10_04_1080p.mp4`, 30:58, 1568x1080, 50308 frames at about 27 fps.
- Proxy (seen): five MP4 segments at 1280x882, one frame per second, 1858 frames in total. Anything that happened between two proxy frames is not visible here.
- The on-screen clock (UTC-4) runs continuously from 17:58:52 to 18:29:49 across all five segments. I found no gaps and no duplicated seconds at the segment boundaries.
- The brief's stated segment boundaries (6:12 each) do not match the files. These are the real lengths:

| File | Frames | On-screen clock | Recording time |
|---|---|---|---|
| part00 | 452 | 17:58:52 – 18:06:23 | 0:00 – 7:32 |
| part01 | 500 | 18:06:24 – 18:14:43 | 7:32 – 15:52 |
| part02 | 250 | 18:14:44 – 18:18:53 | 15:52 – 20:02 |
| part03 | 500 | 18:18:54 – 18:27:13 | 20:02 – 28:22 |
| part04 | 156 | 18:27:14 – 18:29:49 | 28:22 – 30:58 |

- How I read it:
  - Header readouts (clock, chart OHLC, DOM delta header, CVD): every 10th frame, 186 frames, cropped and enlarged.
  - The DOM ladder: viewed close up at about 25 frames chosen around the pre-open, the open, the 18:16 jump, the high, and the fade.
  - Full screen: viewed at about 12 frames.
  - I did not view every one of the 1858 frames at full resolution. Prices quoted below were read off those sampled frames. Between samples, the true high and low may have gone further than these numbers show.
- All five segments were viewable. No stretch of the half hour is missing or reconstructed.

## What is on screen

- **Platform:** openmarket.xyz, browser tab `CME_BTC`. The chart symbol is printed as `CME_F BTCV6`, and the chart footer reads "Source: CME · Real-time". The contract is referred to below only as `BTCV6`, as printed.
- **Chart (left):** a 1-second "Tape" chart.
  - Overlays: VWAP, Order Book Heatmap and Order Book Pressure.
  - Readout: an OHLC line for the current bar.
  - Price: two stepped lines, red above teal. They behave like best offer and best bid, but they are not labeled.
  - Prints: bubbles, some carrying a small number.
  - Resting size: horizontal heatmap bands.
  - Panes: a volume bar pane and a `CVD BTCV6` pane.
- **DOM ladder (right):** columns COB, SVP, DELTA, P/S and PRINTS. The header shows `Δ … · B … / S …`.
  - COB is resting size per price: red offers above, teal bids below. It has a cumulative depth curve and grey shading on some rows. The shading is not labeled, so I don't interpret it.
  - SVP is traded volume per price.
  - DELTA is buy minus sell per price.
  - P/S shows signed changes in resting size per price (the pull/stack column).
  - PRINTS shows cells formatted `N/M.0`. The format is not labeled on screen.
  - In every header I checked, Δ equals B − S. B and S carry no unit label.
- **Header price is stale.** The large price in the chart header reads 85,990.0, then 86,075.0, then 86,425.0, then 86,550.0 (+1.99%). From 18:06:32 to the end it stays at 86,550.0 while the OHLC line and the DOM inside price keep moving. This note uses the OHLC close and the DOM inside row, not the header.
- **Two delta readouts disagree.** The DOM header Δ and the chart's CVD do not track each other. At 18:15:52 to 18:16:02, CVD drops from 48 to 27 while DOM Δ rises from +43 to +46. At 18:26:22 to 18:26:32, CVD drops from 31 to 22 while DOM B, S and Δ are unchanged (+49, B 289 / S 240). The screen doesn't explain why. Below, "delta" means the DOM header Δ, and CVD is cited only as displayed.
- **Unreadable readings stay unreadable.** The OHLC line was mid-redraw and unreadable at 18:02:22, 18:03:42, 18:21:22, 18:22:22 and 18:23:42. Most volume bar heights have no readable value. At the end of part00, a right-click context menu covers part of the chart.

## Walk of the half hour

### part00: 17:58:52 – 18:06:23 (pre-open, open, first range)

- **Pre-open:**
  - The status bar reads "CME opens 2m". The OHLC is frozen at 85990 and the DOM inside row is 85980.
  - The DOM header (Δ +19 · B 86 / S 67) and the SVP/DELTA columns are already populated, carried from before the session.
  - The resting book is thin: 1.00 to 6.00 per level, with one 10.00 offer several levels above the inside.
  - At 17:58:52, P/S shows −7.0 at the 85980 row and −5.0 a few rows lower, but the PRINTS column is empty and the market is not open. **Those are pulls, not fills.**
- **Open:**
  - The first changed OHLC is at 18:00:02 (O 86070, L 86045, C 86045).
  - The PRINTS column fills in around the 86040 and 86070 inside rows, with cells reading 2/1.0, 3/1.0 and 2/2.0.
  - On the offer side, P/S fills with +1.0 to +5.0 entries (size stacking), while the resting COB bars stay at 1.00 to 10.00.
- **Reset:** between 18:00:22 (B 105 / S 70) and 18:00:32 (Δ +16 · B 20 / S 4), the DOM header counters reset, and the SVP/DELTA columns start fresh around 86175. All later B/S figures count from this reset.
- **Price:**
  - It climbs to 86205 by 18:00:52 and 86470 by 18:02:32.
  - It pulls back to 86330 at 18:03:12 and 86265 at 18:03:52.
  - It chops between 86285 and 86435 until 18:06:12, and reads 86405 at 18:06:22.
- **Resting vs executed vs price:**
  - During the 18:00:32 to 18:02:32 climb, B rose from 20 to 64 and S from 4 to 44, so buys led and price rose.
  - From 18:02:32 to 18:06:12, S rose from 44 to 84 (+40) against B from 64 to 95 (+31), so Δ fell from +20 to +11. Price stayed inside 86265–86470 and did not trend down. More selling was executed without price breaking the range low seen in this sample.

### part01: 18:06:24 – 18:14:43 (range near the session's high-volume prices)

- **Price:**
  - 86505 at 18:06:32 and 86540 at 18:07:02.
  - Sags to 86355 at 18:08:42.
  - Then holds 86445–86610 for the rest of the segment. Readings at 86500–86515 recur most often.
- **Delta:** B rose from 104 to 177 (+73) and S from 94 to 142 (+48), so Δ went from +10 to +35. CVD rose from about 15 to about 40.
- **Resting vs executed vs price:** this was the clearest stretch of executed buying that didn't move price. Δ rose by about 25 while price stayed in a band of about 165 points.
  - On the ladder at 18:10:34, resting COB is 1.00 to 7.00 per level on both sides.
  - The SVP column builds its largest values in this band. 21.0 and 24.0 are the biggest SVP numbers I saw in any of the ladders I inspected, and they were already present by 18:16:16.
  - P/S keeps cycling between + and − on both sides.
  - The DOM screenshots don't let me say which side's resting size absorbed the buying. The book shows changes, not who filled against what.

### part02: 18:14:44 – 18:18:53 (the jump)

- **Before the jump:** 86580–86600 until 18:15:52, then 86635 at 18:16:02 and 86660 at 18:16:12.
- **The jump, frame by frame:**

| Clock | Inside row | B | S |
|---|---|---|---|
| 18:16:16 | 86660 | 204 | 158 |
| 18:16:17 | 86680 | 205 | 156 |
| 18:16:18 | 86680 | 210 | 156 |
| 18:16:19 | 86830 | 213 | 159 |
| 18:16:20 | 86850 | 214 | 160 |

  At 18:16:22 the OHLC reads 86865. On the chart, the bid/offer lines go almost vertical from about 86600 to about 86865, with a string of print bubbles up the move. The volume readout for that bar is "Vol 1.00".
- **Resting vs executed vs price:** this was the clearest case of resting size and executed size *not* moving together.
  - At 18:16:17, the offer side above 86680 shows resting levels of 1.00 to 6.00 each, stacked over several dozen ticks.
  - From 18:16:17 to 18:16:20, the B counter rose by about 9 and S by about 4, while price moved about 170 points.
  - After the move, the SVP column at the levels it crossed shows mostly 1.0 entries, with PRINTS cells of 1/1.0 and 2/1.0.
  - So most of the displayed offer between 86680 and 86830 was not executed at those levels. It left the book without printing.
  - At one frame per second I can't see whether it was cancelled outright or moved higher. **It was not filled, and I'm not counting it as volume.**
- **After the jump:**
  - 86745 at 18:16:42, 86900 at 18:17:12, 86820–86855 through 18:18:12, 86905 at 18:18:22, 86875 at 18:18:52.
  - Δ moved from +52 at 18:16:22 to +44 at 18:18:52, with S rising faster (162 to 203) than B (214 to 247).
  - CVD fell from about 34 to about 20–25 over the same stretch.

### part03: 18:18:54 – 18:27:13 (high, then fade)

- **Price:**
  - 86880–86945 through 18:21:12. 86945 at 18:19:52 is the highest reading in my 10-second samples.
  - Drops to 86815 at 18:21:32 and 86805 at 18:21:42.
  - 86800–86845 to 18:23:02, then 86760–86805 to 18:26:12, and 86750 at 18:27:02 and 18:27:12.
- **Delta:** B rose from 249 to 291 (+42) and S from 203 to 241 (+38). Δ stayed between +44 and +50 the whole time. CVD drifted from about 31 down to 22–23, with the unexplained step from 31 to 22 at 18:26:32 noted above.
- **Resting vs executed vs price:**
  - Price gave back about 195 points from the sampled high while the executed buy/sell difference stayed nearly flat.
  - Close-up ladders at 18:19:52, 18:21:27, 18:23:42, 18:26:32 and 18:27:12 show offers of 1.00 to 10.00 per level above the inside, bids of 1.00 to 8.00 below, and P/S in small + and − steps. The largest is ±9.0 near the inside at 18:19:52.
  - I saw no single resting level large enough to account for the fade, and no burst of sell prints in the PRINTS column. The move happened with little change in executed delta.

### part04: 18:27:14 – 18:29:49 (fade into the high-volume prices)

- **Price:** 86690 at 18:27:22, 86650 at 18:28:12, 86610 at 18:28:22, 86580 at 18:29:32, 86515 at 18:29:42. In the last frame (18:29:49), the OHLC reads 86515 and the DOM inside row is 86510.
- **Delta:** B rose from 292 to 305 and S from 244 to 252, so Δ went from +48 to +53. CVD read about 21–26.
- **Resting vs executed vs price:**
  - Price fell about 235 points in this segment while Δ rose by 5.
  - The volume pane shows a few taller bars in the last minute, including one tall red bar, but they carry no readable values.
  - In the final frame, the inside sits at 86510, which is the band where SVP shows 22.0 and 24.0 and PRINTS shows 17/3.0 and 20/3.0. The tape ends back inside the part01 high-volume band.
  - Resting COB at the end is 1.00 to 8.00 per level on both sides.

## Verdict

- **Session shape, as read off the screen:**
  - Pre-open at 85990.
  - First prints near 86040–86070 at 18:00.
  - A range around 86445–86610 from roughly 18:09 to 18:16.
  - A jump of about 190 points in about four seconds, 18:16:16 to 18:16:20.
  - A sampled high of 86945 at 18:19:52.
  - A steady fade back to 86515 by 18:29:49.
  - I sampled every 10th frame, so the true high and low were not checked frame by frame.
- **Where resting size, executed size and price moved together:**
  - The first two minutes after the open: buy-led prints and a rising price.
  - Part of part01: price held inside the high-volume band while SVP built there.
- **Where they did not:**
  - At the 18:16 jump, price crossed displayed offer that mostly did not print. The book thinned and price moved, but executed size was small.
  - The fade from 18:21 to the end: price fell about 430 points while DOM Δ stayed between +44 and +53.
  - From 18:02 to 18:06: more selling was executed without price breaking down.
- **Readouts to trust and not to trust:**
  - Use the DOM header Δ = B − S, which was internally consistent in every frame I checked.
  - Don't use the header price, which was stale from 18:06:32.
  - Don't use CVD as a session delta: it stepped down twice while the DOM counters did not.
- **Not determinable from this proxy:**
  - Anything between frames.
  - Whether vanished resting size was cancelled or repriced.
  - Volume bar values.
  - The meaning of the grey COB shading and of the `N/M.0` PRINTS format.
  - The five OHLC readings that were mid-redraw.
