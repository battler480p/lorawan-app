   
import sqlite3
import json
import pytest
from datetime import datetime, timezone

from app.datastore import DataStore
from app.uplink_parser import UplinkParser
from app.models import SensorReading


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
    assert readings 

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



def test_get_devices_returns_unique_devices_in_last_seen_order(test_db):
    # device-A appears, then device-B appears, then device-A again.
    DataStore.save_raw_only("ok", {"msg": 1}, device_id="device-A")
    DataStore.save_raw_only("ok", {"msg": 2}, device_id="device-B")
    DataStore.save_raw_only("ok", {"msg": 3}, device_id="device-A")

    devices = DataStore.get_devices()

    # unique and ordered by last seen (device-A was last inserted)
    assert devices[0] == "device-A"
    assert "device-B" in devices
    assert len(devices) == 2


def test_get_device_readings(tmp_path, monkeypatch, good_ttn_payload):
    test_db = tmp_path / "test_data.db"
    monkeypatch.setattr(DataStore, "DB_PATH", test_db)

    DataStore.init_db()

    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    assert uplink is not None

    readings = UplinkParser.to_readings(uplink)
    assert readings

    DataStore.save_readings(readings)

    retrieved = DataStore.get_device_readings("device-123", 4)

    assert len(retrieved) == len(readings)

    assert all(isinstance(r, SensorReading) for r in retrieved)

    assert all(r.device_id == "device-123" for r in retrieved)

    by_name = {r.sensor_name: r for r in retrieved}

    assert by_name["temperature"].value == 22.4
    assert by_name["temperature"].unit == "C"


def test_get_device_readings_and_limit(tmp_path, monkeypatch, good_ttn_payload):
    test_db = tmp_path / "test_data.db"
    monkeypatch.setattr(DataStore, "DB_PATH", test_db)

    DataStore.init_db()
    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    assert uplink is not None

    readings = UplinkParser.to_readings(uplink)
    assert readings

    DataStore.save_readings(readings)

    limit = 4
    retrieved = DataStore.get_device_readings("device-123", limit)

    assert len(retrieved) == min(len(readings), limit)
    assert all(isinstance(r, SensorReading) for r in retrieved)
    assert all(r.device_id == "device-123" for r in retrieved)

    by_name = {r.sensor_name: r for r in retrieved}
    assert by_name["temperature"].value == 22.4
    assert by_name["temperature"].unit == "C"

def test_get_device_raw_payloads_filters_by_device_and_orders_desc(test_db):
    # insert payloads in a known order across two devices
    DataStore.save_raw_only("ok", {"n": 1}, device_id="device-A", payload_b64="AAA=")
    DataStore.save_raw_only("ok", {"n": 2}, device_id="device-B", payload_b64="BBB=")
    DataStore.save_raw_only("decoder_error", {"n": 3}, device_id="device-A", payload_b64="CCC=")

    rows = DataStore.get_device_raw_payloads("device-A", limit=50)

    # should only return device-A rows (2 of them)
    assert len(rows) == 2
    assert all(isinstance(r, dict) for r in rows)

    # should be ordered newest-first, so the last inserted for device-A comes first
    assert rows[0]["decode_status"] == "decoder_error"
    assert rows[0]["payload_b64"] == "CCC="
    assert json.loads(rows[0]["raw_json"])["n"] == 3

    assert rows[1]["decode_status"] == "ok"
    assert rows[1]["payload_b64"] == "AAA="
    assert json.loads(rows[1]["raw_json"])["n"] == 1


def test_get_device_raw_payloads_respects_limit(test_db):
    # insert 3 rows for the same device
    DataStore.save_raw_only("ok", {"n": 1}, device_id="device-123")
    DataStore.save_raw_only("ok", {"n": 2}, device_id="device-123")
    DataStore.save_raw_only("ok", {"n": 3}, device_id="device-123")

    rows = DataStore.get_device_raw_payloads("device-123", limit=2)

    assert len(rows) == 2

    # we should get n=3 then n=2
    assert json.loads(rows[0]["raw_json"])["n"] == 3
    assert json.loads(rows[1]["raw_json"])["n"] == 2


def test_get_device_raw_payloads_returns_empty_list_when_none(test_db):
    rows = DataStore.get_device_raw_payloads("missing-device", limit=10)
    assert rows == []


def test_get_device_raw_payloads_dict_shape(test_db):
    DataStore.save_raw_only(
        "unknown_packet",
        {"hello": "world"},
        device_id="device-X",
        payload_b64="AQIDBA==",
        received_at="2026-02-16T06:51:01.132300865Z",
    )

    rows = DataStore.get_device_raw_payloads("device-X", limit=10)
    assert len(rows) == 1

    row = rows[0]
    # required keys 
    assert set(row.keys()) == {
        "id",
        "ingested_at",
        "received_at",
        "decode_status",
        "payload_b64",
        "raw_json",
    }

    assert row["decode_status"] == "unknown_packet"
    assert row["payload_b64"] == "AQIDBA=="
    assert row["received_at"] == "2026-02-16T06:51:01.132300865Z"
    assert json.loads(row["raw_json"]) == {"hello": "world"}

    # ingested_at should exist (default set by SQLite)
    assert isinstance(row["ingested_at"], str)
    assert len(row["ingested_at"]) > 0




























