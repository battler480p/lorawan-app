##demo script for the mqtt class 

import time
import json

from app.mqtt_client import MQTTClient


def handle_uplink(payload: dict) -> None:
    print("\n[DEMO] Uplink received:")
    print(json.dumps(payload, indent=2))


def main() -> int:
    """
    Main demo entry point.
    - Creates an MQTTClient
    - Connects to the broker
    - Runs until Ctrl+C
    """
    # create client with uplink handler
    mqtt_client = MQTTClient(on_uplink=handle_uplink)

    # attempt connection
    try:
        mqtt_client.connect()
    except Exception as err:
        print(f"[DEMO] ERROR: Connection to broker failed: {err}")
        return -1

    print("[DEMO] Connected. Waiting for messages... (Ctrl+C to exit)")

    # main loop 
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[DEMO] Keyboard interrupt detected, shutting down...")
        mqtt_client.disconnect()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
