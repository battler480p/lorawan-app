
class DownlinkEncoder:
    """
    encodes downlink commands into binary payloads
    packet format:
    [CMD][TARGET][LEN][DATA]

    cmd: command identifier (1 byte)
    target: sensor or subsystem (1byte)
    len: number of bytes in data (1byte)
    data: command specific payload
    """

    #COMMAND LIST
    CMD_SET_INTERVAL = 0x01 #set a sensor interval
    CMD_REQUEST_STATUS = 0x02 #send next uplink immediately 
    CMD_GET_REGION = 0x20 #request lora region 
    CMD_SET_REGION = 0x21 #set lora region
    CMD_RESET = 0x22 #reset board

    SENSOR_IDS = {
        "temperature": 0, #bme280
        "humidity": 0,
        "pressure": 0,
        "visible": 1, #si115x
        "ir": 1,
        "wind_vane": 2,
        "wind_speed": 3,
    }

    @staticmethod
    def encode_set_interval(sensor_id: int, interval_minutes: int) -> bytes:
        """
        encode interval update command
        payload: [0x01][sensor_id][0x04][seconds (4bytes, big-endian)]

        args: 
        sensor_id(int) :sensor target id
        interval_minutes (int): interval in minutes)

        returns:
        bytes
        """
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
        """
        encode request status command
        payload: 
        [0x02][0x00][0x00]
        returns: bytes
        """
        return bytes([
            DownlinkEncoder.CMD_REQUEST_STATUS,
            0x00, #blank 
            0x00 #blank 

        ])
    
    @staticmethod
    def encode_reset() -> bytes: 
        """
        encode device reset command
        
        payload:
        [0x22][0x00][0x00]
        
        returns: 
        bytes
        """
        return bytes([
            DownlinkEncoder.CMD_RESET,
            0x00, #blank
            0x00 #blank 

        ])
    
    @staticmethod 
    def encode_get_region() -> bytes: 
        """
        encode request for current lora region

        payload:
        [0x20][0x00][0x00]

        returns:
        bytes
        """
        return bytes([
            DownlinkEncoder.CMD_GET_REGION,
            0x00, #blank
            0x00 #blank
        ])

    @staticmethod 
    def encode_set_region(region: int) -> bytes:
        """
        encode region update command
        payload:
        [0x21][0x00][0x01][region_id]

        args:
        region (int): region id (mapped from REGION_MAP)

        returns:
        bytes
        """
        return bytes([
            DownlinkEncoder.CMD_SET_REGION,
            0x00,   # target
            0x01,   # length
            region  # data
        ])
    
    

    @staticmethod
    def get_sensor_id(sensor_name: str) -> int:
        if sensor_name == "all":
            return 0xFF

        if sensor_name not in DownlinkEncoder.SENSOR_IDS:
            raise ValueError(f"Unknown sensor: {sensor_name}")

        return DownlinkEncoder.SENSOR_IDS[sensor_name]
