
import sqlite3
import json
import pytest
from datetime import datetime, timezone, timedelta

from app.datastore import DataStore
from app.uplink_parser import UplinkParser
from app.models import SensorReading, SensorStats


# -----------------------
# Fixtures / Helpers
# -----------------------

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_data.db"
    monkeypatch.setattr(DataStore, "DB_PATH", db_path)
    DataStore.init_db()
    return db_path


@pytest.fixture
def good_ttn_payload():
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
                "charge_C": 16.777216,
                "accel_x_g": 1.0,
            },
        },
    }


def dt_utc(y, m, d, hh=0, mm=0, ss=0):
    return datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc)


def insert_reading_direct(db_path, device_id, sensor_name, value, unit, measured_at: datetime):
    """Insert reading directly as DB row using ISO string (matches DataStore storage)."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO sensor_readings(device_id, sensor_name, value, unit, measured_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (device_id, sensor_name, value, unit, measured_at.isoformat()),
    )
    conn.commit()
    conn.close()


# -----------------------
# DB Initialization
# -----------------------

def test_init_db_creates_tables(test_db):
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    conn.close()

    assert "sensor_readings" in tables
    assert "raw_payloads" in tables


# -----------------------
# Raw Payload Storage
# -----------------------

def test_save_raw_only_inserts_row_with_metadata(test_db, good_ttn_payload):
    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    assert uplink is not None
    assert isinstance(uplink.received_at, datetime)

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
    cur.execute(
        """
        SELECT raw_json, device_id, received_at, payload_b64, decode_status
        FROM raw_payloads
        WHERE id = ?
        """,
        (raw_id,),
    )
    row = cur.fetchone()
    conn.close()

    assert row is not None
    raw_json_text, device_id, received_at_text, payload_b64, decode_status = row

    assert decode_status == "ok"
    assert device_id == "device-123"
    assert payload_b64 == "AQIDBA=="

    saved = json.loads(raw_json_text)
    assert saved["end_device_ids"]["device_id"] == "device-123"

    # received_at stored as iso string from datetime
    assert received_at_text == uplink.received_at.isoformat()


def test_save_raw_only_inserts_row_without_metadata(test_db, good_ttn_payload):
    raw_id = DataStore.save_raw_only(
        decode_status="invalid_shape",
        raw_json=good_ttn_payload,
    )

    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT device_id, received_at, payload_b64, decode_status
        FROM raw_payloads
        WHERE id = ?
        """,
        (raw_id,),
    )
    row = cur.fetchone()
    conn.close()

    assert row is not None
    device_id, received_at, payload_b64, decode_status = row

    assert decode_status == "invalid_shape"
    assert device_id is None
    assert received_at is None
    assert payload_b64 is None


# -----------------------
# Sensor Readings Storage
# -----------------------

def test_save_sensor_readings_inserts_rows(test_db, good_ttn_payload):
    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    assert uplink is not None

    readings = UplinkParser.to_readings(uplink)
    assert readings

    DataStore.save_readings(readings)

    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT device_id, sensor_name, value, unit, measured_at
        FROM sensor_readings
        """
    )
    rows = cur.fetchall()
    conn.close()

    assert len(rows) == len(readings)

    saved = {(r[1], r[2], r[3]) for r in rows}  # (sensor_name, value, unit)
    expected = {(r.sensor_name, r.value, r.unit) for r in readings}
    assert saved == expected

    expected_ts = uplink.received_at.isoformat()
    for row in rows:
        assert row[4] == expected_ts


# -----------------------
# Simple Queries
# -----------------------

def test_get_devices_returns_unique_devices_in_last_seen_order(test_db):
    DataStore.save_raw_only("ok", {"msg": 1}, device_id="device-A")
    DataStore.save_raw_only("ok", {"msg": 2}, device_id="device-B")
    DataStore.save_raw_only("ok", {"msg": 3}, device_id="device-A")

    devices = DataStore.get_devices()

    assert devices[0] == "device-A"
    assert "device-B" in devices
    assert len(devices) == 2


def test_get_device_readings_returns_models_and_values(test_db, good_ttn_payload):
    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    assert uplink is not None

    readings = UplinkParser.to_readings(uplink)
    DataStore.save_readings(readings)

    retrieved = DataStore.get_device_readings("device-123", limit=100)

    assert len(retrieved) == len(readings)
    assert all(isinstance(r, SensorReading) for r in retrieved)
    assert all(r.device_id == "device-123" for r in retrieved)

    by_name = {r.sensor_name: r for r in retrieved}
    assert by_name["temperature"].value == 22.4
    assert by_name["temperature"].unit == "C"


def test_get_device_raw_payloads_filters_orders_and_limit(test_db):
    DataStore.save_raw_only("ok", {"n": 1}, device_id="device-A", payload_b64="AAA=")
    DataStore.save_raw_only("ok", {"n": 2}, device_id="device-B", payload_b64="BBB=")
    DataStore.save_raw_only("decoder_error", {"n": 3}, device_id="device-A", payload_b64="CCC=")

    rows = DataStore.get_device_raw_payloads("device-A", limit=1)
    assert len(rows) == 1
    assert rows[0]["decode_status"] == "decoder_error"
    assert json.loads(rows[0]["raw_json"])["n"] == 3


# -----------------------
# Recent-per-sensor Query
# -----------------------

def test_get_recent_device_readings_returns_latest_per_sensor(test_db):
    device_id = "device-123"
    t_old = dt_utc(2026, 2, 16, 10, 0, 0)
    t_new = dt_utc(2026, 2, 16, 11, 0, 0)

    DataStore.save_readings([
        SensorReading(device_id=device_id, sensor_name="temp", value=20.0, unit="C", measured_at=t_old),
        SensorReading(device_id=device_id, sensor_name="humi", value=50.0, unit="%", measured_at=t_old),
    ])
    DataStore.save_readings([
        SensorReading(device_id=device_id, sensor_name="temp", value=22.5, unit="C", measured_at=t_new),
        SensorReading(device_id=device_id, sensor_name="humi", value=55.2, unit="%", measured_at=t_new),
    ])

    recent = DataStore.get_recent_device_readings(device_id)
    assert len(recent) == 2

    temp = next(r for r in recent if r.sensor_name == "temp")
    humi = next(r for r in recent if r.sensor_name == "humi")

    assert temp.value == 22.5
    assert humi.value == 55.2

    # Pydantic parses measured_at string -> datetime; compare normalized isoformat
    assert temp.measured_at == t_new


def test_get_recent_device_readings_isolates_by_device(test_db):
    DataStore.save_readings([
        SensorReading(device_id="dev-A", sensor_name="temp", value=10.0, unit="C", measured_at=dt_utc(2026, 2, 16, 10)),
    ])
    DataStore.save_readings([
        SensorReading(device_id="dev-B", sensor_name="temp", value=30.0, unit="C", measured_at=dt_utc(2026, 2, 16, 12)),
    ])

    recent_a = DataStore.get_recent_device_readings("dev-A")
    assert len(recent_a) == 1
    assert recent_a[0].device_id == "dev-A"
    assert recent_a[0].value == 10.0


def test_get_recent_device_readings_empty(test_db):
    assert DataStore.get_recent_device_readings("non-existent-device") == []


# -----------------------
# get_device_sensor_readings
# -----------------------

def test_get_device_sensor_readings_filters_and_orders(test_db):
    t1 = dt_utc(2026, 2, 16, 6)
    t2 = dt_utc(2026, 2, 16, 7)

    insert_reading_direct(test_db, "device-123", "temperature", 20.0, "C", t1)
    insert_reading_direct(test_db, "device-123", "temperature", 21.0, "C", t2)

    insert_reading_direct(test_db, "device-123", "humidity", 50.0, "%", t2)       # exclude
    insert_reading_direct(test_db, "device-999", "temperature", 99.0, "C", t2)    # exclude

    results = DataStore.get_device_sensor_readings("device-123", "temperature", limit=100)
    assert len(results) == 2
    assert results[0].value == 21.0  # newest first
    assert results[1].value == 20.0


def test_get_device_sensor_readings_respects_limit(test_db):
    base = dt_utc(2026, 2, 16, 6)
    insert_reading_direct(test_db, "device-123", "temperature", 20.0, "C", base)
    insert_reading_direct(test_db, "device-123", "temperature", 21.0, "C", base + timedelta(hours=1))
    insert_reading_direct(test_db, "device-123", "temperature", 22.0, "C", base + timedelta(hours=2))

    results = DataStore.get_device_sensor_readings("device-123", "temperature", limit=2)
    assert len(results) == 2
    assert results[0].value == 22.0
    assert results[1].value == 21.0


def test_get_device_sensor_readings_empty_when_no_match(test_db):
    assert DataStore.get_device_sensor_readings("no-such-device", "temperature", limit=10) == []



def test_get_device_sensor_readings_since_filters_by_time_inclusive(test_db):
    device_id = "device-1"
    t0 = dt_utc(2026, 2, 16, 10)
    t1 = dt_utc(2026, 2, 16, 11)
    t2 = dt_utc(2026, 2, 16, 12)

    DataStore.save_readings([
        SensorReading(device_id=device_id, sensor_name="temperature", value=10, unit="C", measured_at=t0),
        SensorReading(device_id=device_id, sensor_name="temperature", value=11, unit="C", measured_at=t1),
        SensorReading(device_id=device_id, sensor_name="temperature", value=12, unit="C", measured_at=t2),
    ])

    since = t1
    results = DataStore.get_device_sensor_readings_since(device_id, "temperature", since)

    # inclusive of t1 and after, ordered ASC
    assert [r.value for r in results] == [11, 12]
    assert results[0].measured_at == t1
    assert results[1].measured_at == t2


def test_get_device_readings_between_filters_inclusive_and_orders_asc(test_db):
    device_id = "device-1"
    t0 = dt_utc(2026, 2, 16, 10)
    t1 = dt_utc(2026, 2, 16, 11)
    t2 = dt_utc(2026, 2, 16, 12)

    DataStore.save_readings([
        SensorReading(device_id=device_id, sensor_name="a", value=1, unit="u", measured_at=t0),
        SensorReading(device_id=device_id, sensor_name="a", value=2, unit="u", measured_at=t1),
        SensorReading(device_id=device_id, sensor_name="a", value=3, unit="u", measured_at=t2),
    ])

    results = DataStore.get_device_readings_between(device_id, start=t0, end=t1)
    # BETWEEN is inclusive; should include t0 and t1, ordered ASC
    assert [r.value for r in results] == [1, 2]
    assert results[0].measured_at == t0
    assert results[1].measured_at == t1


def test_get_device_singlular_sensor_readings_between_filters_sensor_and_time(test_db):
    device_id = "device-1"
    t0 = dt_utc(2026, 2, 16, 10)
    t1 = dt_utc(2026, 2, 16, 11)

    DataStore.save_readings([
        SensorReading(device_id=device_id, sensor_name="temperature", value=10, unit="C", measured_at=t0),
        SensorReading(device_id=device_id, sensor_name="humidity", value=50, unit="%", measured_at=t0),
        SensorReading(device_id=device_id, sensor_name="temperature", value=11, unit="C", measured_at=t1),
    ])

    results = DataStore.get_device_singlular_sensor_readings_between(
        device_id=device_id,
        sensor_name="temperature",
        start=t0,
        end=t1,
    )

    assert [r.value for r in results] == [10, 11]
    assert all(r.sensor_name == "temperature" for r in results)


def test_get_sensor_stats_returns_stats_object(test_db):
    device_id = "device-1"
    t0 = dt_utc(2026, 2, 16, 10)
    t1 = dt_utc(2026, 2, 16, 11)
    t2 = dt_utc(2026, 2, 16, 12)

    DataStore.save_readings([
        SensorReading(device_id=device_id, sensor_name="temperature", value=10.0, unit="C", measured_at=t0),
        SensorReading(device_id=device_id, sensor_name="temperature", value=20.0, unit="C", measured_at=t1),
        SensorReading(device_id=device_id, sensor_name="temperature", value=30.0, unit="C", measured_at=t2),
    ])

    stats = DataStore.get_sensor_stats(device_id, "temperature", start=t0, end=t2)
    assert isinstance(stats, SensorStats)

    assert stats.device_id == device_id
    assert stats.sensor_name == "temperature"
    assert stats.count == 3
    assert stats.min == 10.0
    assert stats.max == 30.0
    assert stats.avg == pytest.approx(20.0)
    assert stats.start == t0
    assert stats.end == t2


def test_get_sensor_stats_returns_none_when_no_rows(test_db):
    device_id = "device-1"
    t0 = dt_utc(2026, 2, 16, 10)
    t1 = dt_utc(2026, 2, 16, 11)

    stats = DataStore.get_sensor_stats(device_id, "temperature", start=t0, end=t1)
    assert stats is None




















