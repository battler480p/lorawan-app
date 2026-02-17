import pytest
from datetime import datetime

from app.uplink_parser import UplinkParser
from app.models import UplinkMessage, SensorReading


@pytest.fixture
def good_ttn_payload():

    # picking a few keys that parser currently supports 
    sensor_keys = list(UplinkParser.SENSORS.keys())
    assert len(sensor_keys) >= 2, "UplinkParser.SENSORS should define at least 2 sensor keys"

    decoded = {
        "packet_type": "temp_humi",
        # add a couple of sensor keys that to_readings should pick up
        sensor_keys[0]: 1.23,
        sensor_keys[1]: 4.56,
    }

    return {
        "end_device_ids": {"device_id": "device-123"},
        "received_at": "2026-02-16T06:51:01.132300865Z",
        "uplink_message": {
            "f_port": 1,
            "frm_payload": "AQIDBA==",  # base64 placeholder
            "decoded_payload": decoded,
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


def test_parse_uplink_missing_decoded_payload_sets_empty_dict(payload_missing_decoded_payload):
    uplink = UplinkParser.parse_uplink(payload_missing_decoded_payload)
    assert uplink is not None
    assert isinstance(uplink.decoded, dict)
    assert uplink.decoded == {}  # decoded_payload missing -> treat as empty


def test_to_readings_returns_expected_readings(good_ttn_payload):
    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    assert uplink is not None

    readings = UplinkParser.to_readings(uplink)
    assert isinstance(readings, list)
    assert all(isinstance(r, SensorReading) for r in readings)

    # only keys that appear in decoded_payload AND exist in SENSORS should be emitted.
    expected_keys_present = [
        k for k in UplinkParser.SENSORS.keys()
        if k in uplink.decoded
    ]
    assert len(readings) == len(expected_keys_present)

    # validate mapping correctness for each  reading
    by_name = {r.sensor_name: r for r in readings}

    for key in expected_keys_present:
        expected_sensor_name, expected_unit = UplinkParser.SENSORS[key]
        assert expected_sensor_name in by_name
        assert by_name[expected_sensor_name].unit == expected_unit
        assert by_name[expected_sensor_name].device_id == "device-123"
        assert by_name[expected_sensor_name].measured_at == uplink.received_at


def test_to_readings_skips_missing_keys(good_ttn_payload):
    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    assert uplink is not None

    # remove one known key from decoded_payload
    some_key = next(iter(UplinkParser.SENSORS.keys()))
    uplink.decoded.pop(some_key, None)

    readings = UplinkParser.to_readings(uplink)
    names = {r.sensor_name for r in readings}

    expected_sensor_name, _ = UplinkParser.SENSORS[some_key]
    assert expected_sensor_name not in names


def test_to_readings_returns_empty_list_when_decoded_is_empty(good_ttn_payload):
    uplink = UplinkParser.parse_uplink(good_ttn_payload)
    assert uplink is not None

    uplink.decoded = {}
    readings = UplinkParser.to_readings(uplink)
    assert readings == []


def test_check_errors_decoder_error():
    decoded_payload = {"error": "Payload too short"}
    assert UplinkParser.check_errors(decoded_payload) == "decoder_error"


def test_check_errors_unknown_packet():
    decoded_payload = {"packet_type": "unknown", "debug_message": "Unknown flag"}
    assert UplinkParser.check_errors(decoded_payload) == "unknown_packet"


def test_check_errors_none_for_known_packet():
    decoded_payload = {"packet_type": "temp_humi", "temperature_c": 25}
    # this should not be considered an error just because packet_type exists
    assert UplinkParser.check_errors(decoded_payload) is None
