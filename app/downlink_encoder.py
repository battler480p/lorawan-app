
class DownlinkEncoder:

    CMD_SET_INTERVAL = 0x02

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
        return bytes([
            DownlinkEncoder.CMD_SET_INTERVAL,
            sensor_id,
            0x02,  # length
            interval_minutes & 0xFF,            # LOW byte
            (interval_minutes >> 8) & 0xFF      # HIGH byte
        ])
    
    @staticmethod
    def get_sensor_id(sensor_name: str) -> int:
        if sensor_name not in DownlinkEncoder.SENSOR_IDS:
            raise ValueError(f"Unknown sensor: {sensor_name}")
        return DownlinkEncoder.SENSOR_IDS[sensor_name]
