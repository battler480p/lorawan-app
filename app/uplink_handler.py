from datetime import datetime
from typing import Optional, Dict, Any, List
from app.models import UplinkMessage
from app.uplink_parser import UplinkParser
from app.datastore import DataStore 


class UplinkHandler: 
    """
    coordinates processing for incoming TTN uplinks. 
    
    """

    @staticmethod
    def handle_uplink(payload):
        """
        process one raw TTN uplink payload.

        the handler always attempts to save the raw payload with a decode status. if the payload contains configured sensor fields, normalized
        SensorReading objects are saved to the database. 

        Args: 
            payload: raw JSON dictionary received from TTN over MQTT
        
            Returns:
                Decode status string, such as "ok", "ok_no_readings",
                "decoder_error," "unknown_packet", or "invalid_shape".
        
        
        """
        uplink = UplinkParser.parse_uplink(payload)
        if uplink is None:
            DataStore.save_raw_only(decode_status='invalid_shape', raw_json=payload)
            status = "invalid_shape"
            return status
        error_status = UplinkParser.check_errors(uplink.decoded)
        if error_status is not None: 
            DataStore.save_raw_only(
                decode_status=error_status,
                raw_json=payload,
                device_id=uplink.device_id,
                received_at=uplink.received_at,
                payload_b64=uplink.raw_b64,
            )
                
            if error_status == "unknown_packet":
                readings = UplinkParser.to_readings(uplink)
                if readings:
                    DataStore.save_readings(readings)

            return error_status

        readings = UplinkParser.to_readings(uplink)
        decode_status = "ok" if readings else "ok_no_readings"

        DataStore.save_raw_only(
            decode_status=decode_status,
            raw_json=payload,
            device_id=uplink.device_id,
            received_at=uplink.received_at,
            payload_b64=uplink.raw_b64,
        )

        if readings:
            DataStore.save_readings(readings)

        return decode_status
    



    