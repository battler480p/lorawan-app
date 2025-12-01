# tests/mqtt_client_tests.py

import json
from types import SimpleNamespace

from app.mqtt_client import MQTTClient


def handle_uplink_collector(collected: list):
    """Factory to capture payloads into a list."""
    def _handler(payload: dict):
        collected.append(payload)
    return _handler


def test_mqtt_client_handles_fake_uplink():
    # prepare a list to collect callbacks
    received = []

    client = MQTTClient(on_uplink=handle_uplink_collector(received))

    # fake TTN-like payload
    sample_payload = {
        "end_device_ids": {
            "device_id": "demo-device",
        },
        "uplink_message": {
            "decoded_payload": {
                "temperature": 23.4,
                "humidity": 50.2,
                "battery": 96,
                "sequence": 12,
            }
        },
    }

    # fake message object
    fake_message = SimpleNamespace(
        topic="test/topic",
        payload=json.dumps(sample_payload).encode("utf-8"),
    )

    # call the internal callback directly
    client._on_message(client.client, None, fake_message)

    #check handler was called exactly once
    assert len(received) == 1

    #check if payload is what we expect
    payload = received[0]
    assert payload["end_device_ids"]["device_id"] == "demo-device"
    assert payload["uplink_message"]["decoded_payload"]["temperature"] == 23.4
    assert payload["uplink_message"]["decoded_payload"]["battery"] == 96


def test_mqtt_client_ignores_invalid_json():
    """_on_message should not crash or call handler on bad JSON."""
    received = []

    client = MQTTClient(on_uplink=handle_uplink_collector(received))

    # payload that is NOT valid JSON
    fake_message = SimpleNamespace(
        topic="test/topic",
        payload=b"this is not json at all",
    )

    # should not raise, and should not call  handler
    client._on_message(client.client, None, fake_message)

    #check handler was never called
    assert len(received) == 0


class FakePahoClient:
    """Simple fake for paho.mqtt.client.Client to test connect/disconnect."""
    def __init__(self):
        self.connected_to = None
        self.loop_started = False
        self.loop_stopped = False
        self.disconnected = False
        self.on_connect = None
        self.on_subscribe = None
        self.on_message = None

    def connect(self, host, port):
        self.connected_to = (host, port)

    def loop_start(self):
        self.loop_started = True

    def loop_stop(self):
        self.loop_stopped = True

    def disconnect(self):
        self.disconnected = True


def test_mqtt_client_connect_and_disconnect_use_underlying_client():
    """
    connect() should call the underlying client's connect() and loop_start(),
    and disconnect() should call loop_stop() and disconnect().
    """
    client = MQTTClient(on_uplink=None)

    # swap out the real paho client with fake one to avoid real network
    fake = FakePahoClient()
    client.client = fake

    # set known host/port to verify they are passed through
    client.host = "test-broker.local"
    client.port = 1883

    client.connect()

    # check if fake client saw the right host/port, and loop started
    assert fake.connected_to == ("test-broker.local", 1883)
    assert fake.loop_started is True

    # call disconnect()
    client.disconnect()

    # check if loop stopped and disconnect was called
    assert fake.loop_stopped is True
    assert fake.disconnected is True


def test_mqtt_client_prints_payload_when_no_handler(capsys):
    """If no on_uplink handler is provided, payload should be printed."""

    client = MQTTClient(on_uplink=None)

    sample_payload = {
        "status": "ok",
        "value": 42
    }

    fake_message = SimpleNamespace(
        topic="test/topic",
        payload=json.dumps(sample_payload).encode("utf-8"),
    )

    # call the internal callback
    client._on_message(client.client, None, fake_message)

    # capture stdout
    captured = capsys.readouterr()

    assert '"status": "ok"' in captured.out
    assert '"value": 42' in captured.out
