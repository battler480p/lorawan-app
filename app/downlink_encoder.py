
class DownlinkEncoder:

    #COMMAND LIST
    CMD_SET_INTERVAL = 0x01 #set a sensor interval
    CMD_REQUEST_STATUS = 0x02 #send next uplink immediately 
    #reset 

    SENSOR_IDS = {
        "temperature": 0,
        "humidity": 0,
        "pressure": 0,
        "visible": 1,
        "ir": 1,
        "wind_vane": 2,
        "wind_speed": 3,
    }

    @staticmethod
    def encode_set_interval(sensor_id: int, interval_minutes: int) -> bytes:
        seconds = interval_minutes * 60
        return bytes([
            DownlinkEncoder.CMD_SET_INTERVAL,
            sensor_id,
            0x04,  # length
            (seconds >> 24) & 0xFF, #big endian 
            (seconds >> 16) & 0xFF,
            (seconds >> 8) & 0xFF,
            seconds & 0xFF,
                        ])
    
    @staticmethod
    def encode_request_status() -> bytes:
        return bytes([
            DownlinkEncoder.CMD_REQUEST_STATUS,
            0x00, #blank 
            0x00 #blank 

        ])
    

    @staticmethod
    def get_sensor_id(sensor_name: str) -> int:
        if sensor_name == "all":
            return 0xFF

        if sensor_name not in DownlinkEncoder.SENSOR_IDS:
            raise ValueError(f"Unknown sensor: {sensor_name}")

        return DownlinkEncoder.SENSOR_IDS[sensor_name]
