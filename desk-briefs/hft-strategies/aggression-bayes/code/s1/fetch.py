"""Download and checksum-verify the S1-LXF-BAR v1.1 inputs from data.binance.vision.

PAPER ONLY. Read-only public archive; no exchange API, no keys.

Usage: python fetch.py --data /tmp/s1data
Writes <data>/fetch_log.csv with one row per file: dataset, date, url, status, sha256, expected.
A file whose sha256 differs from its .CHECKSUM is deleted and logged as CHECKSUM_FAIL.
"""
import argparse
import csv
import datetime as dt
import hashlib
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "https://data.binance.vision/data/"
START = dt.date(2025, 10, 1)
END = dt.date(2026, 10, 1)
S0_DATE = dt.date(2026, 10, 1)

DATASETS = {
    "perp_1m": "futures/um/daily/klines/BTCUSDT/1m/BTCUSDT-1m-{d}.zip",
    "perp_5m": "futures/um/daily/klines/BTCUSDT/5m/BTCUSDT-5m-{d}.zip",
    "metrics": "futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-{d}.zip",
    "spot_1m": "spot/daily/klines/BTCUSDT/1m/BTCUSDT-1m-{d}.zip",
}
S0_DATASETS = {
    "perp_trades": "futures/um/daily/trades/BTCUSDT/BTCUSDT-trades-{d}.zip",
    "perp_aggtrades": "futures/um/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-{d}.zip",
}


def _get(url, retries=4):
    delay = 4
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise
            if attempt == retries:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == retries:
                raise
        time.sleep(delay)
        delay *= 2


def local_path(data_dir, dataset, rel):
    return os.path.join(data_dir, dataset, os.path.basename(rel))


def fetch_one(data_dir, dataset, template, day):
    rel = template.format(d=day.isoformat())
    url = BASE + rel
    path = local_path(data_dir, dataset, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    row = {"dataset": dataset, "date": day.isoformat(), "url": url, "status": "", "sha256": "", "expected": ""}
    try:
        expected = _get(url + ".CHECKSUM").decode().split()[0].strip().lower()
    except Exception as e:  # noqa: BLE001
        row["status"] = f"CHECKSUM_FETCH_FAIL:{type(e).__name__}:{getattr(e, 'code', '')}"
        return row
    row["expected"] = expected
    if os.path.exists(path):
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if h == expected:
            row.update(status="OK", sha256=h)
            return row
    try:
        blob = _get(url)
    except Exception as e:  # noqa: BLE001
        row["status"] = f"DOWNLOAD_FAIL:{type(e).__name__}:{getattr(e, 'code', '')}"
        return row
    h = hashlib.sha256(blob).hexdigest()
    row["sha256"] = h
    if h != expected:
        row["status"] = "CHECKSUM_FAIL"
        if os.path.exists(path):
            os.remove(path)
        return row
    with open(path, "wb") as f:
        f.write(blob)
    row["status"] = "OK"
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()

    jobs = []
    day = START
    while day <= END:
        for ds, tpl in DATASETS.items():
            jobs.append((ds, tpl, day))
        day += dt.timedelta(days=1)
    for ds, tpl in S0_DATASETS.items():
        jobs.append((ds, tpl, S0_DATE))

    with ThreadPoolExecutor(args.workers) as ex:
        rows = list(ex.map(lambda j: fetch_one(args.data, *j), jobs))

    rows.sort(key=lambda r: (r["dataset"], r["date"]))
    with open(os.path.join(args.data, "fetch_log.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    bad = [r for r in rows if r["status"] != "OK"]
    print(f"files: {len(rows)}  ok: {len(rows) - len(bad)}  failed: {len(bad)}")
    for r in bad:
        print("FAIL", r["dataset"], r["date"], r["status"])


if __name__ == "__main__":
    main()
