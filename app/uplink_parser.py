from datetime import datetime
from typing import Optional, Dict, Any, List
from app.models import SensorReading, UplinkMessage
from app.sensor_config import get_sensor_config



class UplinkParser:

    @staticmethod
    def parse_uplink(raw_json) -> UplinkMessage | None:
        """
        parse raw TTN JSON into an UplinkMessage

        Args: 
            raw_json: raw uplink JSON payload from TTN 

        Returns: 
            UplinkMessage if the payload has the expected TTN structure,
            otherwise None
        
        """

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
        """
        convert an UplinkMessage into normalized SensorReading objects. 

        only decoded payload keys listed in config/sensors.json are converted.
        unknown decoded fields are ignored. 

        Args:
            uplink: parsed UplinkMessage containing payload data.
        
        Returns:
            List of SensorReading objects. empty list if no configured fields exist. 
        
        
        """
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
        """
        Check decoded payload for decoder or packet error markers.

        Args: 
            decoded_payload: dictionary from TTN decoded_payload. 

        Returns: 
            Decode status string if an error is found, otherwise None. 
        
        """
       
        if "error" in decoded_payload:
            return "decoder_error"

        packet_type = decoded_payload.get("packet_type")
        if packet_type == "unknown":
            return "unknown_packet"

        return None




        













        


            






