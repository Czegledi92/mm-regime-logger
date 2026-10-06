"""Pixel measurement for 20261006-vwap-tracking-asks.png (paper research only).

Usage: python3 desk-briefs/tape-reads/tools/measure_20261006.py [png]
Prints the price/time fits, every yellow horizontal segment with its price and time span,
line samples every 25 px, and the per-step ask-minus-line table used in the brief.
"""
import json
import sys
import numpy as np
from PIL import Image

PNG = sys.argv[1] if len(sys.argv) > 1 else "desk-briefs/tape-reads/20261006-vwap-tracking-asks.png"
im = np.array(Image.open(PNG).convert("RGB")).astype(int)
R, G, B = im[..., 0], im[..., 1], im[..., 2]
PLOT_X0, PLOT_X1 = 24, 1527  # last drawn bar column
TOOLTIP = (232, 851, 646, 1000)  # x0, x1, y0, y1 of the ladder pop-up (occludes chart)

# Price axis: gray full-width level lines whose values are printed in their tags (READ).
LEVELS = [(269.5, 87220.00), (345.0, 86999.11), (507.0, 86530.00), (770.5, 85766.87), (1044.5, 84972.01)]
ys = np.array([l[0] for l in LEVELS]); vs = np.array([l[1] for l in LEVELS])
b, a = np.polyfit(ys, vs, 1)
resid = vs - (a + b * ys)
price = lambda y: a + b * y

yellow = (R > 200) & (G > 200) & (B < 120)


def yellow_segments(min_len=15):
    segs = []
    for y in range(G.shape[0]):
        xs = np.where(yellow[y, :PLOT_X1 + 1])[0]
        if len(xs) < min_len:
            continue
        s = p = xs[0]
        for x in list(xs[1:]) + [10**9]:
            if x > p + 3:
                if p - s >= min_len:
                    segs.append((y, int(s), int(p)))
                s = x
            p = x
    merged = []
    for y, s, e in segs:
        for m in merged:
            if m["x0"] == s and m["x1"] == e and y - m["y1"] == 1:
                m["y1"] = y
                break
        else:
            merged.append({"y0": y, "y1": y, "x0": s, "x1": e})
    for m in merged:
        m["yc"] = (m["y0"] + m["y1"]) / 2
        m["price"] = round(price(m["yc"]), 2)
    return merged


red = (R > 150) & (G < 120) & (B < 120) & (R - G > 70)
teal = (G > 120) & (R < 110) & (G - R > 50)
line_mask = red | teal


def short_runs(x, y0=380, y1=1100, max_len=3):
    col = line_mask[y0:y1, x]
    out, s = [], None
    for i, v in enumerate(list(col) + [False]):
        if v and s is None:
            s = i
        if not v and s is not None:
            if i - s <= max_len:
                out.append(y0 + (s + i - 1) / 2)
            s = None
    return out


def occluded(x, y):
    return TOOLTIP[0] <= x <= TOOLTIP[1] and y >= TOOLTIP[2] - 3


def trace_line(start_x=PLOT_X1, start_y=761.0, stop_x=PLOT_X0, win=4, grow=1.5):
    """Continuity tracker from start_x toward stop_x; the search window widens with each missed column."""
    track, y, missed = {}, start_y, 0
    step = -1 if stop_x < start_x else 1
    for x in range(start_x, stop_x + step, step):
        if occluded(x, y):
            missed += 1
            continue
        w = win + grow * missed
        c = [r for r in short_runs(x) if abs(r - y) <= w and not occluded(x, r)]
        if c:
            y = min(c, key=lambda r: abs(r - y))
            track[x] = y
            missed = 0
        else:
            missed += 1
    return track


# Time axis: centres of printed tick labels (READ text, x measured): 02:00, 08:00 Oct 5; 02:00, 08:00 Oct 6.
TIME_TICKS = [(189.0, 2.0), (450.0, 8.0), (1233.0, 26.0), (1494.0, 32.0)]
tb, ta = np.polyfit([t[0] for t in TIME_TICKS], [t[1] for t in TIME_TICKS], 1)


def clock(x):
    h = ta + tb * x
    day, h = 5 + int(h // 24), h % 24
    mins = int(round(h * 60))
    return f"Oct {day} {mins // 60:02d}:{mins % 60:02d}"


def line_at(track, x, half=3):
    ys = [track[k] for k in range(x - half, x + half + 1) if k in track]
    return (float(np.median(ys)), max(ys) - min(ys)) if ys else (None, None)


if __name__ == "__main__":
    segs = yellow_segments()
    # The pop-up ladder hides the line between x of about 600 and 851, and the line breaks at x 965-971
    # (20:00 bar), so trace each piece separately.
    track = {**trace_line(PLOT_X0, 466.5, TOOLTIP[0] + 380),
             **trace_line(TOOLTIP[1] + 1, 691.5, 964),
             **trace_line(PLOT_X1, 761.0, 972)}
    segs = [s for s in segs if not (TOOLTIP[0] <= s["x0"] and s["x1"] <= TOOLTIP[1] and s["y0"] >= TOOLTIP[2])]
    for s in segs:
        s["t0"], s["t1"] = clock(s["x0"]), clock(s["x1"])
    samples = {}
    for x in range(PLOT_X0, PLOT_X1 + 1, 25):
        y, spread = line_at(track, x)
        samples[x] = None if y is None else (clock(x), round(y, 1), round(price(y), 1))
    print(json.dumps({"price_fit": {"b_per_px": b, "a": a, "resid": resid.round(2).tolist()},
                      "time_fit_px_per_h": 1 / tb,
                      "segments": segs,
                      "line": samples}, indent=1, default=float))

    # Ask rows (pixel centres) per step and the x column where ask-minus-line is evaluated.
    A, B, C = [556.5, 591.5, 626.0], [487.5, 513.5, 532.5], [472.5, 487.5, 513.5]
    steps = [("A first visible line before occlusion", A, 595), ("A end", A, 881), ("B start", B, 882),
             ("B pre line break", B, 964), ("B post line break", B, 974), ("B Oct 6 line low", B, 1299),
             ("B last before re-quote", B, 1381), ("C first after re-quote", C, 1382), ("C last bar", C, PLOT_X1)]
    print("\nstep | time | line px | line $ | asks $ | ask-line $ | ask-line bps | gaps $")
    for name, rows, x in steps:
        ly, spread = line_at(track, x)
        L = float(price(ly))
        asks = [float(price(r)) for r in rows]
        off = [q - L for q in asks]
        print(name, "|", clock(x), "|", round(ly, 1), f"(spread {spread})", "|", round(L, 1), "|",
              [round(q, 1) for q in asks], "|", [round(o, 1) for o in off], "|",
              [round(o / L * 1e4, 1) for o in off], "|", [round(asks[i] - asks[i + 1], 1) for i in range(2)])
