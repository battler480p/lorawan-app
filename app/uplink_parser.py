from datetime import datetime
from typing import Optional, Dict, Any, List
from app.models import SensorReading, UplinkMessage



class UplinkParser:
    
    SENSORS = {
        "temperature": ("temperature", "C"),
        "humidity": ("humidity", "%"),
        "pressure": ("pressure", "hPa"),
        "sunlight": ("sunlight", "lux"),
        "wind_direction": ("wind_direction", "deg"),
        "wind_speed": ("wind_speed", "km/h"),
        "battery": ("battery", "mV"),

    }



    @staticmethod
    def parse_uplink(raw_json) -> UplinkMessage | None:
        try: 
            device_id = raw_json["end_device_ids"]["device_id"]
            um = raw_json["uplink_message"]
            fport = um["f_port"]
            b64_payload = um["frm_payload"]
            decoded_payload = um["decoded_payload"]
            received_at = um["received_at"]
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



        


            






