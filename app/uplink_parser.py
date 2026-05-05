from datetime import datetime
from typing import Optional, Dict, Any, List
from app.models import SensorReading, UplinkMessage
from app.sensor_config import get_sensor_config



class UplinkParser:

    @staticmethod
    def parse_uplink(raw_json) -> UplinkMessage | None:
        try: 
            device_id = raw_json["end_device_ids"]["device_id"]
            um = raw_json["uplink_message"]
            fport = um["f_port"]
            b64_payload = um["frm_payload"]
            decoded_payload = um.get("decoded_payload") or {}
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
        sensor_defs = get_sensor_config().get_reading_defs()

        for key, (sensor_name, unit) in sensor_defs.items():
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




        













        


            






