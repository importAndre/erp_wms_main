from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import Any, Dict, Iterable

import pandas as pd


STOCK_UPDATE_FILE = Path(__file__).resolve().parents[2] / "stock_to_update.csv"
STOCK_UPDATE_COLUMNS = ["sku", "stock", "date", "needs_update"]

_file_lock = RLock()


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "sim"}


def write_stock_updates(data: Dict[str, Dict[str, Any]]) -> int:
    """Replace the stock update queue with the latest full-stock response."""
    rows = [
        {
            "sku": sku,
            "stock": values.get("stock", 0),
            "date": values.get("date"),
            "needs_update": True,
        }
        for sku, values in data.items()
    ]
    frame = pd.DataFrame(rows, columns=STOCK_UPDATE_COLUMNS)
    with _file_lock:
        frame.to_csv(STOCK_UPDATE_FILE, index=False)
    return len(frame)


def read_stock_updates() -> Dict[str, Dict[str, Any]]:
    if not STOCK_UPDATE_FILE.exists():
        return {}

    with _file_lock:
        frame = pd.read_csv(STOCK_UPDATE_FILE, dtype={"sku": str})

    if not set(STOCK_UPDATE_COLUMNS).issubset(frame.columns):
        return {}

    # A partially written or otherwise malformed CSV row must not prevent every
    # product from being refreshed.  Coerce stock values once and discard only
    # rows that cannot represent a valid stock update.
    frame["stock"] = pd.to_numeric(frame["stock"], errors="coerce")
    frame = frame.dropna(subset=["sku", "stock", "date", "needs_update"])

    return {
        row["sku"]: {
            "stock": int(row["stock"]),
            "date": row["date"],
            "needs_update": _as_bool(row["needs_update"]),
        }
        for _, row in frame.iterrows()
    }


def mark_stock_updates_done(skus: Iterable[str]) -> None:
    completed = set(skus)
    # print(completed)
    if not completed or not STOCK_UPDATE_FILE.exists():
        return

    with _file_lock:
        frame = pd.read_csv(STOCK_UPDATE_FILE, dtype={"sku": str})
        if not set(STOCK_UPDATE_COLUMNS).issubset(frame.columns):
            return
        frame.loc[frame["sku"].isin(completed), "needs_update"] = False
        frame.to_csv(STOCK_UPDATE_FILE, index=False)
