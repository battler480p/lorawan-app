import pytest
from datetime import datetime


from app.uplink_parser import UplinkParser
from app.models import UplinkMessage, SensorReading


@pytest.fixture
def good_ttn_payload():
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


@pytest.fixture
def payload_missing_device_id(good_ttn_payload):
    p = dict(good_ttn_payload)
    p["end_device_ids"] = {}  # missing device_id
    return p


@pytest.fixture
def payload_missing_uplink_message(good_ttn_payload):
    p = dict(good_ttn_payload)
    p.pop("uplink_message", None)
    return p


@pytest.fixture
def payload_missing_decoded_payload(good_ttn_payload):
    p = dict(good_ttn_payload)
    p["uplink_message"] = dict(p["uplink_message"])
    p["uplink_message"].pop("decoded_payload", None)
    return p


def test_parse_uplink_success(good_ttn_payload):
    uplink = UplinkParser.parse_uplink(good_ttn_payload)

    assert uplink is not None
    assert isinstance(uplink, UplinkMessage)

    assert uplink.device_id == "device-123"
    assert uplink.fport == 1
    assert uplink.raw_b64 == "AQIDBA=="
    assert isinstance(uplink.decoded, dict)

  
    assert isinstance(uplink.received_at, datetime)


def test_parse_uplink_missing_device_id_returns_none(payload_missing_device_id):
    uplink = UplinkParser.parse_uplink(payload_missing_device_id)
    assert uplink is None


def test_parse_uplink_missing_uplink_message_returns_none(payload_missing_uplink_message):
    uplink = UplinkParser.parse_uplink(payload_missing_uplink_message)
    assert uplink is None


def test_parse_uplink_missing_decoded_payload_returns_none(payload_missing_decoded_payload):
    uplink = UplinkParser.parse_uplink(payload_missing_decoded_payload)
    assert uplink is None


def test_to_readings_returns_expected_readings(good_ttn_payload):
    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    assert uplink is not None

    readings = UplinkParser.to_readings(uplink)
    assert isinstance(readings, list)

    # only sensors present in decoded_payload and also listed in SENSORS should appear.
    assert len(readings) == 7
    assert all(isinstance(r, SensorReading) for r in readings)

    # create lookup by sensor_name for easy assertions
    by_name = {r.sensor_name: r for r in readings}

    assert by_name["temperature"].value == 22.4
    assert by_name["temperature"].unit == "C"
    assert by_name["temperature"].device_id == "device-123"

    assert by_name["humidity"].value == 58.1
    assert by_name["humidity"].unit == "%"

    assert by_name["pressure"].value == 1016.8
    assert by_name["pressure"].unit == "hPa"

    assert by_name["sunlight"].value == 1234
    assert by_name["sunlight"].unit == "lux"

    assert by_name["wind_speed"].value == 12.3
    assert by_name["wind_speed"].unit == "km/h"

    assert by_name["wind_direction"].value == 270
    assert by_name["wind_direction"].unit == "deg"

    assert by_name["battery"].value == 3920
    assert by_name["battery"].unit == "mV"  

    # all readings should share the uplink timestamp
    for r in readings:
        assert r.measured_at == uplink.received_at


def test_to_readings_skips_missing_keys(good_ttn_payload):
    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    assert uplink is not None

    # Remove some keys from decoded_payload
    uplink.decoded.pop("pressure", None)
    uplink.decoded.pop("sunlight", None)

    readings = UplinkParser.to_readings(uplink)
    names = {r.sensor_name for r in readings}

    assert "pressure" not in names
    assert "sunlight" not in names
    assert "temperature" in names
    assert "humidity" in names


def test_to_readings_returns_empty_list_when_decoded_is_empty(good_ttn_payload):
    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    assert uplink is not None

    uplink.decoded = {}  # simulate empty decoded payload

    readings = UplinkParser.to_readings(uplink)
    assert readings == []
