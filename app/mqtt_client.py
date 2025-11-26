import json
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from typing import Callable, Optional

# load environment variables from .env
load_dotenv()

class MQTTClient:
    def __init__(self, on_uplink: Optional[Callable[[dict], None]] = None):
        """
        on_uplink: optional callback that receives decoded JSON messages
        """
        self.host = os.getenv("TTN_MQTT_HOST")
        self.port = int(os.getenv("TTN_MQTT_PORT", "8883"))
        self.username = os.getenv("TTN_MQTT_USERNAME")
        self.api_key = os.getenv("TTN_MQTT_API_KEY")
        self.topic = os.getenv("TTN_MQTT_TOPIC")

        self.on_uplink = on_uplink

#create paho client 
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="lorawan_app_client"
        )
#set auth + TLS 
        self.client.username_pw_set(self.username, self.api_key)
        self.client.tls_set()

        # wire callbacks
        self.client.on_connect = self._on_connect
        self.client.on_subscribe = self._on_subscribe
        self.client.on_message = self._on_message

    #MQTT callbacks

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"[MQTT] Connected with result code {reason_code}")
        if self.topic:
            client.subscribe(self.topic)
            print(f"[MQTT] Subscribed to {self.topic}")

    def _on_subscribe(self, client, userdata, mid, reason_codes, properties):
        print(f"[MQTT] Subscription confirmed: {mid}")

    def _on_message(self, client, userdata, message):
        print(f"[MQTT] Message received on {message.topic}")

        try:
            payload = json.loads(message.payload.decode())
        except Exception as e:
            print("[MQTT] Invalid JSON payload:", e)
            return

        # if app provided a handler, forward message
        if self.on_uplink:
            self.on_uplink(payload)
        else:
            print(json.dumps(payload, indent=2))

    #public methods 

    def connect(self):
        print("[MQTT] Connecting to broker...")
        self.client.connect(self.host, self.port)
        self.client.loop_start()

    def disconnect(self):
        print("[MQTT] Disconnecting...")
        self.client.loop_stop()
        self.client.disconnect()

   # def publish_downlink(), will implement later 