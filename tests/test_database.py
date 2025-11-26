import sqlite3
from pathlib import Path
from typing import Iterable 
from datetime import datetime, timezone 

from app.datastore import DataStore


def test_init_db_creates_tables(tmp_path, monkeypatch):
    # using temp db 
    test_db = tmp_path / "test_data.db"
    monkeypatch.setattr(DataStore, "DB_PATH", test_db)

    # call init_db on the modified path
    DataStore.init_db()

    # connect directly with sqlite3 to inspect tables
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    conn.close()

    assert "sensor_readings" in tables
    assert "raw_payloads" in tables


def test_save_raw_only_inserts_row(tmp_path, monkeypatch):
    #  using temp db
    test_db = tmp_path / "test_data.db"
    monkeypatch.setattr(DataStore, "DB_PATH", test_db)

    # init DB and insert one raw payload row
    DataStore.init_db()
    now = datetime.now(timezone.utc) 

    DataStore.save_raw_only(
        device_id="node-1",
        raw_b64="AAEC",
        received_at=now,
        status="decode_missing",
    )

    # verify one row exists in raw_payloads
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT device_id, payload_b64, decode_status FROM raw_payloads")
    rows = cur.fetchall()
    conn.close()

    assert len(rows) == 1
    device_id, payload_b64, decode_status = rows[0]
    assert device_id == "node-1"
    assert payload_b64 == "AAEC"
    assert decode_status == "decode_missing"