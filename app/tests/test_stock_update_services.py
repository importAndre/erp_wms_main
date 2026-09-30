import pandas as pd

from app.services import stockUpdateServices


def test_write_read_and_complete_stock_updates(tmp_path, monkeypatch):
    csv_path = tmp_path / "stock_to_update.csv"
    monkeypatch.setattr(stockUpdateServices, "STOCK_UPDATE_FILE", csv_path)
    response = {
        "KIT.3X200.12XSUP40.BR": {
            "stock": 0,
            "date": "2026-09-17T01:59:13.413881-03:00",
        },
        "42.COLA.200G": {
            "stock": 28,
            "date": "2026-09-17T01:59:37.137056-03:00",
        },
    }

    assert stockUpdateServices.write_stock_updates(response) == 2
    rows = stockUpdateServices.read_stock_updates()
    assert rows["42.COLA.200G"]["stock"] == 28
    assert all(row["needs_update"] for row in rows.values())

    stockUpdateServices.mark_stock_updates_done(["42.COLA.200G"])

    rows = stockUpdateServices.read_stock_updates()
    assert rows["KIT.3X200.12XSUP40.BR"]["needs_update"] is True
    assert rows["42.COLA.200G"]["needs_update"] is False
    assert list(pd.read_csv(csv_path).columns) == [
        "sku",
        "stock",
        "date",
        "needs_update",
    ]


def test_read_stock_updates_ignores_malformed_rows(tmp_path, monkeypatch):
    csv_path = tmp_path / "stock_to_update.csv"
    csv_path.write_text(
        "sku,stock,date,needs_update\n"
        "VALID.SKU,12,2026-09-24T01:50:54-03:00,True\n"
        "3:00,True,,\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(stockUpdateServices, "STOCK_UPDATE_FILE", csv_path)

    assert stockUpdateServices.read_stock_updates() == {
        "VALID.SKU": {
            "stock": 12,
            "date": "2026-09-24T01:50:54-03:00",
            "needs_update": True,
        }
    }
