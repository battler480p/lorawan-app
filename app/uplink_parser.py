from datetime import datetime
from typing import Optional, Dict, Any, List
from app.models import SensorReading, UplinkMessage



class UplinkParser:
    #current sensors, some are going to be changed, added or whatever! 
    SENSORS = {
        "temperature_c": ("temperature", "C"),
        "humidity_percent": ("humidity", "%"),
        "pressure_hpa": ("pressure", "hpa"),
        "wind_speed_mph": ("wind_speed", "mph"),
        "ir": ("infrared", "counts"),
        "visible": ("visible_light", "lux"),
        "wind_vane_angle": ("wind_direction", "deg"),
        "battery_mV": ("battery", "mV"),
       # "pressure": ("pressure", "hPa"),
       # "sunlight": ("sunlight", "lux"),
       # "wind_direction": ("wind_direction", "deg"),
       # "wind_speed": ("wind_speed", "km/h"),
       # "battery": ("battery", "mV"),

    }



    @staticmethod
    def parse_uplink(raw_json) -> UplinkMessage | None:
        try: 
            device_id = raw_json["end_device_ids"]["device_id"]
            um = raw_json["uplink_message"]
            fport = um["f_port"]
            b64_payload = um["frm_payload"]
            decoded_payload = um.get("decoded_payload", {})
            received_at = raw_json.get("received_at") or um.get("received_at")
        except KeyError:
            return None
        
        uplink = UplinkMessage(
            device_id = device_id,
            fport = fport,
            decoded = decoded_payload,
            raw_b64 = b64_payload,
            received_at= received_at,

        )

        return uplink 
    
    @staticmethod
    def to_readings(uplink) -> list[SensorReading]:
        decoded = uplink.decoded


        if not decoded:
            return []
        
        readings: list[SensorReading] = []

        for key, (sensor_name, unit) in UplinkParser.SENSORS.items():
            if key in decoded:
                reading = SensorReading(
                    device_id = uplink.device_id,
                    sensor_name = sensor_name,
                    value=decoded[key],
                    unit=unit,
                    measured_at=uplink.received_at,
                )

                readings.append(reading)
        
        return readings


    @staticmethod
    def check_errors(decoded_payload):
       
        if "error" in decoded_payload:
            return "decoder_error"

        packet_type = decoded_payload.get("packet_type")
        if packet_type == "unknown":
            return "unknown_packet"

        return None




        













        


            






