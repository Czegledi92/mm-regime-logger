"""S2 episodes (spec section 3): the S1 v1.1 events for develop and validate, rebuilt with the S1 code.

PAPER ONLY. Writes <work>/episodes_s1.parquet, <work>/s1_cells.csv and <work>/oi.npy, and checks test T9
(rebuilt rows equal the committed S1 events.parquet) and the frozen lean-cell set.
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "s1"))
import s1  # noqa: E402
import tests_s1  # noqa: E402

SCORED = ["develop", "validate"]
KEEP = ["event_id", "kind", "is_placebo", "offset", "offset_bp", "placebo_dropped", "eligible", "split", "date", "open_time", "g",
        "L", "s", "level_type", "box", "tsib_bucket", "cluster_id", "instance_id", "clock_ok", "impulse", "cal_blocked", "hour_utc",
        "dow", "speed15", "dist_vwap_sigma", "ib_width_rel", "vwap_slope30", "touch_seq", "TI_t", "TI_into", "pen_t", "pen_class",
        "cl_t", "vz_t", "atsz_t", "oi_d5c", "oi_na", "Y_level", "Y_fwd_3", "regime_tag"]
T9_COLS = ["open_time", "L", "s", "kind", "clock_ok", "Y_level", "Y_fwd_3"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--s1data", required=True)
    ap.add_argument("--s1results", required=True)
    ap.add_argument("--work", required=True)
    args = ap.parse_args()
    os.makedirs(args.work, exist_ok=True)
    b1, _b5, _man, _md, _fmt = s1.load_all(args.s1data)
    cfg = s1.Cfg()
    boxes = s1.build_boxes(b1)
    with np.errstate(divide="ignore", invalid="ignore"):
        lv = np.where(b1.v > 0, np.log(b1.v), np.nan)
        la = np.where((b1.v > 0) & (b1.n > 0), np.log(b1.v / b1.n), np.nan)
    z_v, z_ats = s1.robust_z_by_hour(b1, lv), s1.robust_z_by_hour(b1, la)
    ev, ctx, realL = s1.build_events(b1, boxes, cfg)
    ev = s1.add_features(ev, b1, boxes, ctx, cfg, realL, z_v, z_ats)
    ev = ev[ev["split"].isin(SCORED)].copy()
    assert not (ev["split"] == "test").any()

    real_clock = ev[(~ev["is_placebo"]) & ev["eligible"] & ev["clock_ok"]]
    cells, prior = s1.fit_level_model(real_clock, SCORED)
    lean = cells[cells["lean"]]
    lean_set = sorted(f"{r.level_type}|{r.box}|{r.s}|{r.tsib_bucket}:{r.H_L}" for r in lean.itertuples())
    committed = pd.read_csv(os.path.join(args.s1results, "h1_cells.csv"))
    cl = committed[committed["lean"]]
    committed_set = sorted(f"{r.level_type}|{r.box}|{r.s}|{r.tsib_bucket}:{r.H_L}" for r in cl.itertuples())
    lean_ok = lean_set == committed_set

    ref = pd.read_parquet(os.path.join(args.s1results, "events.parquet"))
    ref = ref[ref["split"].isin(SCORED)].set_index("event_id").sort_index()
    mine = ev.set_index("event_id").sort_index()
    same_ids = ref.index.equals(mine.index)
    col_ok = {}
    for c in T9_COLS:
        a, b = mine[c].reindex(ref.index), ref[c]
        if a.dtype.kind == "f" or b.dtype.kind == "f":
            col_ok[c] = bool(np.array_equal(a.to_numpy(float), b.to_numpy(float), equal_nan=True))
        else:
            col_ok[c] = bool((a.astype(str).to_numpy() == b.astype(str).to_numpy()).all())
    t9 = {"same_event_ids": bool(same_ids), "n_rows": int(len(mine)), **{f"equal_{c}": v for c, v in col_ok.items()},
          "lean_cells_equal": bool(lean_ok), "lean_cells": lean_set}
    print(json.dumps(t9, indent=2))

    out = ev[KEEP].copy()
    out["date"] = out["date"].astype(str)
    out.to_parquet(os.path.join(args.work, "episodes_s1.parquet"), index=False)
    cells.to_csv(os.path.join(args.work, "s1_cells.csv"), index=False)
    np.save(os.path.join(args.work, "oi.npy"), b1.oi)
    with open(os.path.join(args.work, "t9.json"), "w") as f:
        json.dump(t9, f, indent=2)
    t8_pass, t8_detail = tests_s1.t9(b1, {"boxes": boxes, "events": ev})
    with open(os.path.join(args.work, "t8.json"), "w") as f:
        json.dump({"pass": bool(t8_pass), "detail": t8_detail}, f, indent=2)
    print("T8", t8_pass, t8_detail)
    if not (same_ids and all(col_ok.values()) and lean_ok):
        print("T9 FAIL")
        sys.exit(1)
    print("T9 PASS")


if __name__ == "__main__":
    main()
