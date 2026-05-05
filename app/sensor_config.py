"""
Sensor configuration loader 

this module loads sensor and region mappings from config/sensors.json

the config file: 
- maps TTN decoded payload fields to normalized sensor names and units
- mapping sensor names to MCU target IDS for downlink commands
- maps LoRa region names to MCU region IDs
"""


import json
from pathlib import Path
from functools import lru_cache
from typing import Any

#path to sensor config file
CONFIG_PATH = Path("config/sensors.json")


class SensorConfig:
    """
    wrapper around the sensor config JSON file 
    """
    def __init__(self, data: dict[str, Any]):
        self.data = data
        self.sensors = data.get("sensors", {})
        self.regions = data.get("regions", {})

    def get_reading_defs(self) -> dict[str, tuple[str, str]]:
        """
        returns:
            {
                "temperature_c": ("temperature", "C"),
                ...
            }
        """
        return {
            decoded_key: (cfg["name"], cfg["unit"])
            for decoded_key, cfg in self.sensors.items()
        }

    def get_sensor_id(self, sensor_name: str) -> int:
        """
        Return the MCU target ID for a normalized sensor name. 

        The name 'all' maps to 0xFF, which tells the MCU to apply the command to every sensor

        args: 
            sensor_name: normalized sensor name, such as "temperature", or "all" 
        
        returns: 
            MCU target ID for the sensor 


        raises:
            ValueError: if the sensor is unknown or does not support downlinks
        """
        if sensor_name == "all":
            return 0xFF

        for cfg in self.sensors.values():
            if cfg["name"] == sensor_name:
                target_id = cfg.get("target_id")

                if target_id is None:
                    raise ValueError(
                        f"Sensor '{sensor_name}' does not support downlink commands"
                    )

                return int(target_id)

        raise ValueError(f"Unknown sensor: {sensor_name}")

    def get_region_id(self, region: str) -> int:
        """
        Return the current LoRA region set
        
        raises:
            ValueError: if the region is invalid
            
        """
        region = region.upper()

        if region not in self.regions:
            raise ValueError(
                f"Invalid region. Options: {list(self.regions.keys())}"
            )

        return int(self.regions[region])


@lru_cache
def get_sensor_config() -> SensorConfig:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return SensorConfig(data)