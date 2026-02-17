from datetime import datetime
from typing import Optional, Dict, Any, List
from app.models import UplinkMessage
from app.uplink_parser import UplinkParser
from app.datastore import DataStore 


class UplinkHandler: 

    @staticmethod
    def handle_uplink(payload):
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
    

    # @staticmethod
    # def process_and_store(payload, uplink, status):
    #     readings = UplinkParser.to_readings(uplink)
    #     device_id = uplink.device_id
    #     raw_b64 = uplink.raw_b64,
    #     received_at = uplink.received_at
    #     fport = uplink.fport 
    #     seq = uplink.seq 
    #     decoded = uplink.decoded
    #     DataStore.save_raw_only(device_id, raw_b64, received_at, status)
    #     DataStore.save_readings(readings) 



    