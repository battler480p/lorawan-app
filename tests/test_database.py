   
import sqlite3
import json
import pytest
from datetime import datetime, timezone

from app.datastore import DataStore
from app.uplink_parser import UplinkParser


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_data.db"
    monkeypatch.setattr(DataStore, "DB_PATH", db_path)
    DataStore.init_db()
    return db_path


@pytest.fixture
def good_ttn_payload():
    # using keys that current parser supports
    return {
        "end_device_ids": {"device_id": "device-123"},
        "received_at": "2026-02-16T06:51:01.132300865Z",
        "uplink_message": {
            "f_port": 1,
            "frm_payload": "AQIDBA==",
            "decoded_payload": {
                "packet_type": "temp_humi",
                "temperature_c": 22.4,
                "humidity_percent": 58.1,
                # include some other supported keys too
                "charge_C": 16.777216,
                "accel_x_g": 1.0,
            },
        },
    }


def test_init_db_creates_tables(test_db):
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    conn.close()

    assert "sensor_readings" in tables
    assert "raw_payloads" in tables


def test_save_raw_only_inserts_row_with_metadata(test_db, good_ttn_payload):
    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    assert uplink is not None

    raw_id = DataStore.save_raw_only(
        decode_status="ok",
        raw_json=good_ttn_payload,
        device_id=uplink.device_id,
        received_at=uplink.received_at,
        payload_b64=uplink.raw_b64,
    )
    assert isinstance(raw_id, int)

    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("""
        SELECT raw_json, device_id, received_at, payload_b64, decode_status
        FROM raw_payloads
        WHERE id = ?
    """, (raw_id,))
    row = cur.fetchone()
    conn.close()

    assert row is not None
    raw_json_text, device_id, received_at_text, payload_b64, decode_status = row

    assert decode_status == "ok"
    assert device_id == "device-123"
    assert payload_b64 == "AQIDBA=="

    # raw_json is stored as JSON text
    saved = json.loads(raw_json_text)
    assert saved["end_device_ids"]["device_id"] == "device-123"

    # received_at is stored as text (isoformat if datetime)
    assert isinstance(received_at_text, str)
    assert len(received_at_text) > 0


def test_save_raw_only_inserts_row_without_metadata(test_db, good_ttn_payload):
    # simulate invalid_shape: store only raw_json + status (others NULL)
    raw_id = DataStore.save_raw_only(
        decode_status="invalid_shape",
        raw_json=good_ttn_payload,
    )

    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("""
        SELECT device_id, received_at, payload_b64, decode_status
        FROM raw_payloads
        WHERE id = ?
    """, (raw_id,))
    row = cur.fetchone()
    conn.close()

    assert row is not None
    device_id, received_at, payload_b64, decode_status = row

    assert decode_status == "invalid_shape"
    assert device_id is None
    assert received_at is None
    assert payload_b64 is None


def test_save_sensor_readings_inserts_rows(test_db, good_ttn_payload):
    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    assert uplink is not None

    readings = UplinkParser.to_readings(uplink)
    assert readings  # should not be empty for this fixture

    DataStore.save_readings(readings)

    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("""
        SELECT device_id, sensor_name, value, unit, measured_at
        FROM sensor_readings
    """)
    rows = cur.fetchall()
    conn.close()

    # expect one row per reading returned by to_readings
    assert len(rows) == len(readings)

    # validate saved rows
    saved = {(r[1], r[2], r[3]) for r in rows}  # (sensor_name, value, unit)
    expected = {(r.sensor_name, r.value, r.unit) for r in readings}
    assert saved == expected

    # all measured_at should match uplink.received_at.isoformat() if datetime
    if hasattr(uplink.received_at, "isoformat"):
        expected_ts = uplink.received_at.isoformat()
        for row in rows:
            assert row[4] == expected_ts

















