from datetime import datetime
from pydantic import ValidationError
import pytest

from app.models import (
    UplinkMessage,
    SensorReading,
    DownlinkCommand,
    IntervalRequest
)

# UplinkMessage

def test_uplink_message_valid():
    msg = UplinkMessage(
        device_id="node-1",
        decoded={"temperature_c": 22.5},
        raw_b64="AAEC",
        received_at=datetime.now()
    )

    assert msg.device_id == "node-1"
    assert msg.decoded["temperature_c"] == 22.5


def test_uplink_message_missing_required_field():
    with pytest.raises(ValidationError):
        UplinkMessage(
            decoded={"temperature_c": 22.5},
            raw_b64="AAEC",
            received_at=datetime.now()
        )  # device_id is missing


# SensorReading

def test_sensor_reading_valid():
    r = SensorReading(
        device_id="node-1",
        sensor_name="temperature",
        value=21.3,
        unit="C",
        measured_at=datetime.now(),
    )

    assert r.value == 21.3
    assert r.unit == "C"


def test_sensor_reading_type_validation():
    with pytest.raises(ValidationError):
        SensorReading(
            device_id="node-1",
            sensor_name="temperature",
            value="not-a-number",  # invalid
            unit="C",
            measured_at=datetime.now(),
        )


# DownlinkCommand

def test_downlink_command_valid():
    cmd = DownlinkCommand(
        device_id="node-1",
        command="set_interval",
        params={"interval_seconds": 60},
        requested_at=datetime.now()
    )

    assert cmd.command == "set_interval"
    assert cmd.params["interval_seconds"] == 60