"""Cross-check for the X1 grid cell M60 x bar-analogue rule against S1 v1.1. PAPER ONLY.

On clock M60 the bar-analogue rule uses the same prints as S1, so its classifications and its AGREE set
should equal S1's event for event. Writes <results>/m60_bar_vs_s1.csv.
Usage: python check_m60_bar.py --work /tmp/s2work --results ../../results/s2
"""
import argparse
import os

import numpy as np
import pandas as pd

import s2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--results", required=True)
    args = ap.parse_args()
    ep, _qc, kept = s2.load(args.work)
    sec = s2.build_seconds(args.work, kept)
    oi = np.load(os.path.join(args.work, "oi.npy"))
    cells = pd.read_csv(os.path.join(args.work, "s1_cells.csv"))
    lean = {(r.level_type, r.box, int(r.s), r.tsib_bucket): r.H_L for r in cells.itertuples() if r.lean}
    f = s2.clock_frame(ep, "M60", sec, {60: s2.hour_blocks(sec, 60)}, {}, oi, np.full(len(ep), np.nan))
    r = s2.apply_rule(f, "bar")
    use = (ep["tape_ok"] & ep["eligible"] & ~ep["placebo_dropped"]).to_numpy()
    agg = ep["TI_into"] >= s2.TI_THR
    ref = {"confirm_RESPECT": agg & (ep["cl_t"] >= 0) & (ep["vz_t"] >= 0), "confirm_BREAK": agg & (ep["cl_t"] < 0) & (ep["vz_t"] >= 0),
           "print_ok": ep["vz_t"] >= 0, "liq_veto_5m": (ep["oi_d5c"] < 0) & (ep["TI_t"].abs() >= 0.20)}
    rows = [{"check": f"{k}: events classified differently from S1", "n": int(use.sum()),
             "value": int((r[k].to_numpy(bool)[use] != v.to_numpy(bool)[use]).sum())} for k, v in ref.items()]
    rows.append({"check": "max |vz_w - vz_t|", "n": int(use.sum()),
                 "value": float(np.nanmax(np.abs(f["vz_w"].to_numpy()[use] - ep["vz_t"].to_numpy()[use])))})
    lab = s2.labels(sec["mid"], f["kd"].to_numpy(), ep["s"].to_numpy(float), ep["L"].to_numpy(float), 1)
    real, _plac = s2.frames(ep, f, r, lab, s2.H_PRIMARY)
    gate, _et, _gp = s2.full_gate(real, lean, s2.H_PRIMARY)
    g1 = pd.read_parquet(os.path.join(args.results, "..", "s1_v1.1", "gate_log.parquet"))
    for sp in s2.SCORED:
        mine = set(gate.loc[gate["AGREE"] & (gate["split"] == sp), "event_id"])
        s1a = set(g1.loc[g1["AGREE"] & (g1["split"] == sp), "event_id"])
        rows.append({"check": f"AGREE event ids {sp}: M60 x bar / S1 / in both", "n": len(mine), "value": f"{len(s1a)} / {len(mine & s1a)}"})
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(args.results, "m60_bar_vs_s1.csv"), index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
