import sqlite3
from pathlib import Path
from typing import Iterable 
from datetime import datetime, timezone 

from app.datastore import DataStore
from app.uplink_parser import UplinkParser
import pytest


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


@pytest.fixture
def good_ttn_payload():
    # Minimal TTN-like structure with decoded_payload
    return {
        "end_device_ids": {"device_id": "device-123"},
        "uplink_message": {
            "f_port": 1,
            "frm_payload": "AQIDBA==",  # base64 placeholder
            "decoded_payload": {
                "temperature": 22.4,
                "humidity": 58.1,
                "pressure": 1016.8,
                "wind_speed": 12.3,
                "wind_direction": 270,
                "sunlight": 1234,
                "battery": 3920,
            },
            "received_at": "2026-02-01T20:14:32.123Z",
        },
    }








def test_save_sensor_readings(tmp_path, monkeypatch, good_ttn_payload):
    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    readings = UplinkParser.to_readings(uplink)
    test_db = tmp_path / "test_data.db"
    monkeypatch.setattr(DataStore, "DB_PATH", test_db)
    DataStore.init_db()
    now = datetime.now(timezone.utc) 
    DataStore.save_readings(readings)
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT device_id, sensor_name, value, unit, measured_at FROM sensor_readings")
    rows = cur.fetchall()
    conn.close()

    assert len(rows) == 7
    sensor1id, sensor1_name, sensor1value, sensor1unit, sensor1datetime = rows[0]
    assert sensor1id == "device-123"
    assert sensor1_name == "temperature"
    assert sensor1value == 22.4
    assert sensor1unit == "C"
    assert sensor1datetime == uplink.received_at.isoformat()

    sensor2id, sensor2_name, sensor2value, sensor2unit, sensor2datetime = rows[1]
    assert sensor2id == "device-123"
    assert sensor2_name == "humidity"
    assert sensor2value == 58.1
    assert sensor2unit == "%"
    assert sensor2datetime == uplink.received_at.isoformat()

















