"""Shared helpers for S2-LXT-1S (level x 1 s tape). PAPER ONLY.

Read-only public archive (data.binance.vision); no exchange API, no keys, no orders.
"""
from __future__ import annotations

import hashlib
import os
import time
import urllib.error
import urllib.request
import zipfile

import numpy as np
import pyarrow.csv as pacsv

BASE = "https://data.binance.vision/data/"
TRADES_TPL = "futures/um/daily/trades/BTCUSDT/BTCUSDT-trades-{d}.zip"
AGG_TPL = "futures/um/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-{d}.zip"
TRADE_COLS = ["id", "price", "qty", "quote_qty", "time", "is_buyer_maker"]
AGG_COLS = ["agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id", "transact_time", "is_buyer_maker"]


def _get(url, retries=4):
    delay = 4
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404 or attempt == retries:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == retries:
                raise
        time.sleep(delay)
        delay *= 2


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_verified(data_dir, dataset, template, day):
    """Download one archive file and verify it against its .CHECKSUM. Returns a log row.
    A file whose sha256 differs is deleted and logged as CHECKSUM_FAIL."""
    rel = template.format(d=day)
    url = BASE + rel
    path = os.path.join(data_dir, dataset, os.path.basename(rel))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    row = {"dataset": dataset, "date": day, "url": url, "path": path, "status": "", "sha256": "", "expected": "", "bytes": 0}
    try:
        expected = _get(url + ".CHECKSUM").decode().split()[0].strip().lower()
    except Exception as e:  # noqa: BLE001
        row["status"] = f"CHECKSUM_FETCH_FAIL:{type(e).__name__}:{getattr(e, 'code', '')}"
        return row
    row["expected"] = expected
    if os.path.exists(path) and sha256_file(path) == expected:
        row.update(status="OK", sha256=expected, bytes=os.path.getsize(path))
        return row
    try:
        blob = _get(url)
    except Exception as e:  # noqa: BLE001
        row["status"] = f"DOWNLOAD_FAIL:{type(e).__name__}:{getattr(e, 'code', '')}"
        return row
    h = hashlib.sha256(blob).hexdigest()
    row["sha256"] = h
    row["bytes"] = len(blob)
    if h != expected:
        row["status"] = "CHECKSUM_FAIL"
        if os.path.exists(path):
            os.remove(path)
        return row
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(blob)
    os.replace(tmp, path)
    row["status"] = "OK"
    return row


def _read_zip(path, cols):
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:
            head = f.read(64).decode(errors="replace")
    has_header = head.split(",")[0].strip() == cols[0]
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:
            ro = pacsv.ReadOptions(column_names=None if has_header else cols, block_size=1 << 26)
            tab = pacsv.read_csv(f, read_options=ro)
    return tab, has_header


def read_trades(path):
    """Raw perp trades as numpy arrays, sorted by id. qty_m is integer thousandths of a BTC."""
    tab, has_header = _read_zip(path, TRADE_COLS)
    tid = tab.column("id").to_numpy().astype(np.int64)
    px = tab.column("price").to_numpy().astype(np.float64)
    qty = tab.column("qty").to_numpy().astype(np.float64)
    tm = tab.column("time").to_numpy().astype(np.int64)
    ibm = tab.column("is_buyer_maker").to_numpy()
    if ibm.dtype != bool:
        ibm = np.char.lower(ibm.astype(str)) == "true"
    o = np.argsort(tid, kind="stable")
    if not np.all(o == np.arange(len(o))):
        tid, px, qty, tm, ibm = tid[o], px[o], qty[o], tm[o], ibm[o]
    return {"id": tid, "price": px, "qty_m": np.rint(qty * 1000).astype(np.int64), "time": tm,
            "ibm": ibm.astype(bool), "has_header": has_header}


def read_aggtrades(path):
    tab, has_header = _read_zip(path, AGG_COLS)
    aid = tab.column("agg_trade_id").to_numpy().astype(np.int64)
    o = np.argsort(aid, kind="stable")
    ibm = tab.column("is_buyer_maker").to_numpy()
    if ibm.dtype != bool:
        ibm = np.char.lower(ibm.astype(str)) == "true"
    return {"agg_id": aid[o], "price": tab.column("price").to_numpy().astype(np.float64)[o],
            "qty_m": np.rint(tab.column("quantity").to_numpy().astype(np.float64) * 1000).astype(np.int64)[o],
            "first_id": tab.column("first_trade_id").to_numpy().astype(np.int64)[o],
            "last_id": tab.column("last_trade_id").to_numpy().astype(np.int64)[o],
            "time": tab.column("transact_time").to_numpy().astype(np.int64)[o], "ibm": ibm.astype(bool)[o],
            "has_header": has_header}


def sweep_groups(t):
    """Taker-order groups from raw trades: maximal runs, in trade-id order, with the same millisecond
    `time` and the same aggressor side. Trade-id gaps do not split a run: the public file omits single
    ids that aggTrades ranges still cover. A group is a sweep when it fills at 2 or more distinct
    prices. Returns per-trade group id and per-group arrays."""
    tid, tm, ibm, px = t["id"], t["time"], t["ibm"], t["price"]
    n = len(tid)
    new = np.ones(n, bool)
    if n > 1:
        new[1:] = (tm[1:] != tm[:-1]) | (ibm[1:] != ibm[:-1])
    gid = np.cumsum(new) - 1
    ng = int(gid[-1]) + 1 if n else 0
    pchg = np.zeros(n, bool)
    if n > 1:
        pchg[1:] = (px[1:] != px[:-1]) & ~new[1:]
    n_px = 1 + np.bincount(gid, weights=pchg, minlength=ng).astype(np.int64)
    up = np.zeros(n, bool)
    dn = np.zeros(n, bool)
    if n > 1:
        up[1:] = (px[1:] > px[:-1]) & ~new[1:]
        dn[1:] = (px[1:] < px[:-1]) & ~new[1:]
    nonmono = (np.bincount(gid, weights=up, minlength=ng) > 0) & (np.bincount(gid, weights=dn, minlength=ng) > 0)
    first = np.flatnonzero(new)
    last = np.r_[first[1:] - 1, n - 1] if n else first
    return {"gid": gid, "first": first, "last": last, "n_px": n_px, "qty_m": np.bincount(gid, weights=t["qty_m"], minlength=ng).astype(np.int64),
            "time": tm[first] if n else tm, "ibm": ibm[first] if n else ibm, "nonmono": nonmono}


def agg_sweep_groups(a):
    """The program's aggTrades definition: consecutive aggTrades with the same transact_time and side,
    spanning 2 or more distinct prices."""
    aid, tm, ibm, px = a["agg_id"], a["time"], a["ibm"], a["price"]
    n = len(aid)
    new = np.ones(n, bool)
    if n > 1:
        new[1:] = (tm[1:] != tm[:-1]) | (ibm[1:] != ibm[:-1])
    gid = np.cumsum(new) - 1
    ng = int(gid[-1]) + 1 if n else 0
    pchg = np.zeros(n, bool)
    if n > 1:
        pchg[1:] = (px[1:] != px[:-1]) & ~new[1:]
    n_px = 1 + np.bincount(gid, weights=pchg, minlength=ng).astype(np.int64)
    first = np.flatnonzero(new)
    return {"gid": gid, "n_px": n_px, "qty_m": np.bincount(gid, weights=a["qty_m"], minlength=ng).astype(np.int64),
            "time": tm[first], "ibm": ibm[first], "first_trade_id": a["first_id"][first],
            "last_trade_id": a["last_id"][np.r_[first[1:] - 1, n - 1]]}
